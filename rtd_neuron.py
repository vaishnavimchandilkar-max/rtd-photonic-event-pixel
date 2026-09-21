"""
rtd_neuron.py
-------------
A minimal model of a photonic-electronic RESONANT TUNNELLING DIODE (RTD) neuron,
the building block of the TU/e PhI group's neuromorphic-photonics work
(cf. Hejda et al., Nanophotonics 2023; Al-Taai et al., NCE 2023).

It reproduces the three signatures of a biological neuron:
  1. an excitability THRESHOLD  (weak optical input -> nothing; strong -> a spike)
  2. a nanosecond SPIKE that returns to rest
  3. a REFRACTORY period (two pulses too close together -> only one spike)

Physics in one paragraph:
  An RTD has an N-shaped current-voltage (I-V) curve. The middle branch has
  NEGATIVE differential resistance (more voltage -> LESS current). Biased just
  outside that unstable region, the device sits at a stable rest point. A small
  optical pulse adds photocurrent that nudges it; if the nudge is big enough to
  push it into the unstable branch, the circuit makes one large, self-limiting
  excursion -- a spike -- then relaxes back. That is exactly leaky-integrate-
  and-fire behaviour, in hardware, at GHz speeds.

Author: Vaishnavi  |  Day-1 mini-project for the TU/e application
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq


# ----------------------------------------------------------------------
# 1. The RTD current-voltage characteristic  I_rtd(V)
#    A resonant-tunnelling "peak" (Gaussian bump) sitting on a rising
#    thermal "valley" current. Representative shape; PVCR ~ 2.3.
# ----------------------------------------------------------------------
def I_rtd(V):
    V = np.asarray(V, dtype=float)
    bump   = 0.8e-3 * np.exp(-((V - 0.45) / 0.13) ** 2)     # resonant peak
    valley = 0.05e-3 * (np.exp((V - 0.30) / 0.18) - 1.0)    # valley / thermal tail
    valley = np.where(valley > 0, valley, 0.0)
    return bump + valley


# ----------------------------------------------------------------------
# 2. Circuit dynamics (two coupled ODEs)
#       C dV/dt  = I_L - I_rtd(V) + I_opt(t)     (fast: voltage across RTD)
#       L dI_L/dt = V_bias - V - R * I_L         (slow: inductor current)
#    This is the standard RTD relaxation/excitable circuit; reducing it
#    gives the FitzHugh-Nagumo neuron model.
# ----------------------------------------------------------------------
C   = 2.0e-12     # F   (2 pF)
L   = 2.4e-6      # H
R   = 560.0       # ohm
Vb  = 0.68        # V   bias -> stable rest just below the I-V peak

# Resting operating point (no light): where the load line meets the I-V curve
Vrest  = brentq(lambda V: (Vb - V) / R - I_rtd(V), 0.0, 0.44)
ILrest = (Vb - Vrest) / R


def simulate(pulses, tmax=140e-9):
    """pulses = list of (t0, amplitude, width) optical Gaussian inputs."""
    def I_opt(t):
        return sum(amp * np.exp(-((t - t0) / w) ** 2) for t0, amp, w in pulses)

    def rhs(t, y):
        V, IL = y
        return [(IL - I_rtd(V) + I_opt(t)) / C,
                (Vb - V - R * IL) / L]

    return solve_ivp(rhs, [0, tmax], [Vrest, ILrest],
                     max_step=5e-12, rtol=1e-9, atol=1e-13, dense_output=True)


def firing_threshold():
    """Bisection search for the smallest optical amplitude that triggers a spike."""
    lo, hi = 0.1e-3, 0.8e-3
    for _ in range(30):
        mid = (lo + hi) / 2
        if simulate([(20e-9, mid, 2e-9)]).y[0].max() - Vrest > 0.15:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


if __name__ == "__main__":
    thr = firing_threshold()
    print(f"Resting voltage      : {Vrest:.3f} V")
    print(f"Firing threshold     : {thr*1e3:.3f} mA (optical-equivalent photocurrent)")
    s = simulate([(20e-9, 1.4*thr, 2e-9)])
    print(f"Spike peak voltage   : {s.y[0].max():.3f} V")
