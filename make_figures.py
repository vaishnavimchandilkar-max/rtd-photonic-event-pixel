"""
make_figures.py — regenerates both figures in figures/ from the models.
Run:  python make_figures.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

HERE = os.path.dirname(os.path.abspath(__file__))
FIG  = os.path.join(HERE, "figures"); os.makedirs(FIG, exist_ok=True)
BLUE="#1f5fbf"; RED="#c1272d"; ORANGE="#e8820c"; GREY="#5a5a5a"; GREEN="#1f9e5a"
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,
                     "figure.dpi":130,"axes.titleweight":"bold"})

# ============ FIGURE 1: single RTD neuron ============
from rtd_neuron import I_rtd, simulate, firing_threshold, Vrest, ILrest, Vb, R
thr=firing_threshold()
fig=plt.figure(figsize=(13,8.5))
gs=GridSpec(3,2,figure=fig,width_ratios=[1.15,1],height_ratios=[1,1,1],
            hspace=0.55,wspace=0.28,left=0.07,right=0.97,top=0.9,bottom=0.08)
axA=fig.add_subplot(gs[:,0])
V=np.linspace(0,1.05,2000); I=I_rtd(V)*1e3
axA.plot(V,I,color=BLUE,lw=2.6,label="RTD I–V characteristic")
mpk=V<0.6; ip=np.argmax(I[mpk]); mvl=(V>0.5)&(V<0.95); iv=np.where(mvl)[0][np.argmin(I[mvl])]
axA.scatter([V[ip]],[I[ip]],color=RED,zorder=5,s=70); axA.annotate("PEAK",(V[ip],I[ip]),textcoords="offset points",xytext=(8,8),color=RED,fontweight="bold")
axA.scatter([V[iv]],[I[iv]],color=GREEN,zorder=5,s=70); axA.annotate("VALLEY",(V[iv],I[iv]),textcoords="offset points",xytext=(6,-16),color=GREEN,fontweight="bold")
axA.axvspan(V[ip],V[iv],color=ORANGE,alpha=0.16)
axA.annotate("NEGATIVE differential\nresistance (unstable)\n= the 'firing' zone",(0.55,0.72),color="#a35a00",fontsize=9.5,ha="center")
axA.plot(V,(Vb-V)/R*1e3,color=GREY,lw=1.4,ls="--",label="load line (bias)")
axA.scatter([Vrest],[ILrest*1e3],color="black",zorder=6,s=60)
axA.annotate("resting\npoint",(Vrest,ILrest*1e3),textcoords="offset points",xytext=(-46,2),fontsize=9.5,fontweight="bold")
axA.set_xlim(0,1.05); axA.set_ylim(0,1.05); axA.set_xlabel("Voltage across RTD  (V)"); axA.set_ylabel("Current  (mA)")
axA.set_title("A.  The RTD I–V curve: an N-shape with a negative-resistance zone"); axA.legend(loc="upper left",fontsize=9,frameon=False)
axB=fig.add_subplot(gs[0,1])
s=simulate([(20e-9,0.5*thr,2e-9),(60e-9,1.4*thr,2e-9)])
t=np.linspace(0,120e-9,6000); tn=t*1e9
axB.plot(tn,s.sol(t)[0],color=BLUE,lw=2.2); axB.axhline(Vrest,color=GREY,ls=":",lw=1)
axBt=axB.twinx(); opt=(0.5*thr*np.exp(-((t-20e-9)/2e-9)**2)+1.4*thr*np.exp(-((t-60e-9)/2e-9)**2))*1e3
axBt.fill_between(tn,0,opt,color=ORANGE,alpha=0.35); axBt.set_ylim(0,thr*1e3*4); axBt.set_yticks([])
axB.annotate("weak pulse\n→ no spike",(20,Vrest+0.02),fontsize=8.5,color="#a35a00",ha="center")
axB.annotate("strong pulse\n→ SPIKE",(60,0.55),fontsize=8.5,color=RED,ha="center",fontweight="bold")
axB.set_ylabel("RTD voltage (V)"); axB.set_xlabel("time (ns)"); axB.set_title("B.  Threshold: only a strong optical pulse fires"); axB.set_ylim(0.3,0.9)
def refr(sep,ax,title,tmax=90e-9):
    s=simulate([(20e-9,1.4*thr,2e-9),(20e-9+sep,1.4*thr,2e-9)],tmax=tmax)
    t=np.linspace(0,tmax,6000); ax.plot(t*1e9,s.sol(t)[0],color=BLUE,lw=2.2)
    for tp in [20e-9,20e-9+sep]: ax.axvline(tp*1e9,color=ORANGE,ls="--",lw=1.3)
    ax.set_ylim(0.3,0.9); ax.set_ylabel("RTD voltage (V)"); ax.set_xlabel("time (ns)"); ax.set_title(title)
axC=fig.add_subplot(gs[1,1]); refr(4e-9,axC,"C.  Two pulses 4 ns apart → 1 spike  (2nd blocked)")
axC.annotate("2nd pulse lands in\nrefractory period",(30,0.45),fontsize=8.5,color=GREY)
axD=fig.add_subplot(gs[2,1]); refr(8e-9,axD,"D.  Two pulses 8 ns apart → 2 spikes  (recovered)")
fig.suptitle("A photonic RTD neuron, simulated from the group's device model",fontsize=13.5,fontweight="bold",y=0.965)
fig.savefig(os.path.join(FIG,"rtd_neuron_day1.png"),bbox_inches="tight"); plt.close(fig)

# ============ FIGURE 2: ON/OFF event pixel ============
import rtd_event_pixel as px
TMAX=260e-9
on=px.run_neuron(px.drive_on,TMAX); off=px.run_neuron(px.drive_off,TMAX)
t_on=px.spike_times(on,TMAX); t_off=px.spike_times(off,TMAX)
t=np.linspace(0,TMAX,4000); tn=t*1e9
fig=plt.figure(figsize=(11,8.6))
gs=GridSpec(4,1,figure=fig,height_ratios=[1.1,1,1,0.7],hspace=0.42,left=0.10,right=0.96,top=0.9,bottom=0.09)
ax0=fig.add_subplot(gs[0]); P=np.array([px.brightness(tt) for tt in t])
ax0.plot(tn,P,color="black",lw=2.4); ax0.fill_between(tn,0,P,color="gold",alpha=0.15)
ax0.set_ylabel("Brightness\nseen by pixel"); ax0.set_ylim(0,2.4); ax0.set_title("What the pixel is watching (one shared optical input)")
for x,lbl,c in [(40,"brighter",ORANGE),(120,"dimmer",BLUE),(190,"flick +",ORANGE),(215,"flick −",BLUE)]:
    ax0.annotate(lbl,(x,2.15),fontsize=8,color=c,ha="center")
ax1=fig.add_subplot(gs[1]); ax1.plot(tn,on.sol(t)[0],color=BLUE,lw=2); ax1.axhline(Vrest,color=GREY,ls=":",lw=1)
ax1.set_ylabel("ON neuron\nvoltage (V)"); ax1.set_ylim(0.3,0.9)
ax1.set_title("ON neuron  —  fires when brightness INCREASES  (valley-biased RTD)",color=ORANGE,fontsize=11.5)
ax2=fig.add_subplot(gs[2]); ax2.plot(tn,off.sol(t)[0],color=RED,lw=2); ax2.axhline(Vrest,color=GREY,ls=":",lw=1)
ax2.set_ylabel("OFF neuron\nvoltage (V)"); ax2.set_ylim(0.3,0.9)
ax2.set_title("OFF neuron  —  fires when brightness DECREASES  (peak-biased RTD)",color=BLUE,fontsize=11.5)
ax3=fig.add_subplot(gs[3])
for x in t_on*1e9:  ax3.vlines(x,0,1,color=ORANGE,lw=2.5)
for x in t_off*1e9: ax3.vlines(x,0,-1,color=BLUE,lw=2.5)
ax3.axhline(0,color="black",lw=0.8); ax3.set_ylim(-1.4,1.4); ax3.set_yticks([1,-1]); ax3.set_yticklabels(["ON","OFF"])
ax3.set_xlabel("time (ns)"); ax3.set_title("Pixel output: a stream of ON / OFF events (this is what leaves the chip)")
for a in [ax0,ax1,ax2,ax3]: a.set_xlim(0,260)
fig.suptitle("A photonic ON/OFF event pixel from two RTD neurons  —  proposed extension, simulated",fontsize=12.5,fontweight="bold",y=0.965)
fig.savefig(os.path.join(FIG,"rtd_event_pixel_day2.png"),bbox_inches="tight"); plt.close(fig)
print("both figures regenerated ->", os.listdir(FIG))
