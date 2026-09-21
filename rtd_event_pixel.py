"""
rtd_event_pixel.py
------------------
PROPOSED photonic ON/OFF event pixel, built from two RTD neurons.

Idea (an architecture proposal, not a claimed discovery):
  A single RTD neuron biased below its I-V peak fires on optical INCREASES;
  biased above the peak it fires on optical DROPS  -- both behaviours are
  already reported by the TU/e / Strathclyde group. Here we COMBINE them:
  feed one shared, change-sensing optical front-end into two complementary
  neurons so the pixel emits a proper ON/OFF event stream (brighter -> ON
  event, dimmer -> OFF event), exactly like an electronic Dynamic Vision
  Sensor pixel -- but in the group's photonic RTD platform, and (the target
  of the vacancy) as an InP coupon heterogeneously integrated on silicon.

  The shared front-end responds to the RATE OF CHANGE of brightness (a
  change detector, as in a DVS pixel and in the group's own
  signal-minus-delayed-copy edge-detection scheme). Its positive part drives
  the ON neuron; its negative part drives the OFF neuron.

This script drives the pixel with a changing-brightness waveform and prints
the ON/OFF event stream.  Companion figure: make_pixel_fig.py
"""

import numpy as np
from scipy.integrate import solve_ivp
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rtd_neuron import I_rtd, Vb, R, C, L, Vrest, ILrest, firing_threshold

THR = firing_threshold()          # single-neuron firing threshold (photocurrent)
GAIN = 3.0 * THR                  # front-end gain: a typical edge -> supra-threshold

# ---- 1. A changing-brightness input P(t) (a scene the pixel is watching) ----
def brightness(t):
    t = t*1e9  # ns
    def step(t0, w): return 0.5*(1+np.tanh((t-t0)/w))
    P  = 1.0
    P += 1.0*step(40, 3)      # edge appears: brightens
    P -= 1.0*step(120, 3)     # edge leaves: darkens
    P += 0.6*step(190, 1.5)   # fast flicker up
    P -= 0.6*step(215, 1.5)   # fast flicker down
    return P

def dP_dt(t, h=2e-12):
    return (brightness(t+h)-brightness(t-h))/(2*h)

# ---- 2. Shared change-sensing front-end -> complementary ON / OFF drives ----
def drive_on(t):  return GAIN*np.maximum(dP_dt(t), 0.0) / 3e8   # scale dP/dt(ns) -> current
def drive_off(t): return GAIN*np.maximum(-dP_dt(t), 0.0) / 3e8

# ---- 3. One RTD neuron, driven by a given optical-current function ----
def run_neuron(drive, tmax):
    def rhs(t, y):
        V, IL = y
        return [(IL - I_rtd(V) + drive(t)) / C, (Vb - V - R*IL) / L]
    return solve_ivp(rhs, [0, tmax], [Vrest, ILrest],
                     max_step=5e-12, rtol=1e-9, atol=1e-13, dense_output=True)

def spike_times(sol, tmax, level=None):
    level = (Vrest+0.15) if level is None else level
    t = np.linspace(0, tmax, 40000); V = sol.sol(t)[0]
    idx = np.where((V[:-1] < level) & (V[1:] >= level))[0]
    return t[idx]

if __name__ == "__main__":
    TMAX = 260e-9
    on  = run_neuron(drive_on,  TMAX)
    off = run_neuron(drive_off, TMAX)
    t_on, t_off = spike_times(on, TMAX), spike_times(off, TMAX)
    print("ON  events (brightening) at ns:", np.round(t_on*1e9, 1))
    print("OFF events (dimming)     at ns:", np.round(t_off*1e9, 1))
