"""Generates static/images/foregrounds_sed.png
(run: python scripts/foregrounds_figure.py out.png; needs numpy matplotlib camb pillow).

Frequency dependence of the CMB and foregrounds, in CMB thermodynamic units (D_ell, uK^2):
  Top    - temperature, small scales (ell = 3000): ACT DR6 baseline foreground model
           (Louis et al. 2025; Beringue, Surrao et al. 2025, arXiv:2506.06274):
           a_tSZ = 3.35, a_kSZ = 1.48, a_c = 3.69, a_p = 7.65, a_s = 2.86 uK^2 at 150 GHz,
           beta_p = beta_c = 1.87, T_CIB = 9.6 K, beta_s = -2.78 (radio, flux ~ nu^(beta_s+2)).
  Bottom - B-mode polarisation, large scales (ell = 80): BICEP/Keck BK18 (arXiv:2110.00483):
           A_d,353 = 4.4 (+0.8 -0.7) uK^2, beta_d = 1.49, T_d = 19.6 K; A_sync,23 < 1.4 uK^2 (95%),
           beta_s = -3.1. CMB lensing B-modes and r = 0.01 from CAMB.
"""
import sys
import numpy as np, camb
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

out = sys.argv[1]
h, k, Tcmb = 6.62607015e-34, 1.380649e-23, 2.7255

def x_(nu): return h*nu*1e9/(k*Tcmb)
def dBdT(nu):                       # dB_nu/dT at T_CMB (arbitrary normalisation)
    x = x_(nu); return x**4*np.exp(x)/(np.exp(x)-1)**2
def g(nu): return 1/dBdT(nu)        # intensity -> CMB temperature
def B(nu, T):                       # Planck law (arbitrary normalisation)
    return (nu*1e9)**3/(np.exp(h*nu*1e9/(k*T))-1)
def mbb(nu, beta, T):               # modified blackbody in CMB units
    return (nu*1e9)**beta*B(nu, T)*g(nu)
def f_tsz(nu):
    x = x_(nu); return x/np.tanh(x/2)-4
def rj2cmb(nu):                     # RJ temperature -> CMB temperature
    return g(nu)*(nu*1e9)**2

nu = np.logspace(np.log10(20), np.log10(450), 600)

# ---- CMB from CAMB ----
pars = camb.set_params(H0=67.5, ombh2=0.022, omch2=0.12, As=2.1e-9, ns=0.965, tau=0.054,
                       r=0.01, WantTensors=True, lmax=4000, lens_potential_accuracy=1)
res = camb.get_results(pars)
cl = res.get_cmb_power_spectra(pars, CMB_unit="muK", raw_cl=False)
D_TT_3000 = cl["total"][3000, 0]
D_BB_lens_80 = cl["lensed_scalar"][80, 2]
D_BB_r_80 = cl["tensor"][80, 2]

# ---- top: ACT DR6 extragalactic foregrounds at ell = 3000 ----
n0 = 150.
tsz  = 3.35*(f_tsz(nu)/f_tsz(n0))**2
ksz  = 1.48*np.ones_like(nu)
cib  = (3.69+7.65)*(mbb(nu, 1.87, 9.6)/mbb(n0, 1.87, 9.6))**2
radio = 2.86*(g(nu)/g(n0))**2*(nu/n0)**(2*(-2.78+2))

# ---- bottom: BK18 polarised foregrounds at ell = 80 ----
def dust_sed(nu, beta=1.49): return (nu*1e9)**beta*B(nu, 19.6)*g(nu)
dust = lambda A: A*(dust_sed(nu)/dust_sed(353.))**2
sync_lim = 1.4*((nu/23.)**-3.1*rj2cmb(nu)/rj2cmb(23.))**2

plt.rcParams.update({"font.family": "serif", "font.size": 16, "mathtext.fontset": "dejavuserif"})
fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.4, 8.2))
fig.subplots_adjust(left=0.16, right=0.97, top=0.95, bottom=0.08, hspace=0.42)
C = dict(cmb="black", tsz="#2166ac", ksz="#555555", cib="#d6604d", radio="#1b7837",
         dust="#d6604d", sync="#1b7837")

def bands(ax, centres, label, ylab, frac=0.25, color="#e8e8e8"):
    for c in centres:
        ax.axvspan(c*(1-frac/2), c*(1+frac/2), color=color, zorder=0, lw=0)
    ax.text(150, ylab, label, fontsize=12, color="#777", ha="center", va="center")

# top panel
bands(a1, [93, 148, 220], "ACT bands", 1500)
a1.axhline(D_TT_3000, color=C["cmb"], lw=2.4)
a1.plot(nu, ksz, color=C["ksz"], lw=2, ls="--")
a1.plot(nu, tsz, color=C["tsz"], lw=2.4)
a1.plot(nu, cib, color=C["cib"], lw=2.4)
a1.plot(nu, radio, color=C["radio"], lw=2.4)
a1.set_title(r"Temperature, small scales ($\ell = 3000$)", fontsize=16)
a1.set_ylim(0.1, 3e3)

# bottom panel
bands(a2, [27, 39, 93, 145, 225, 280], "SO-SAT bands", 12)
a2.axhline(D_BB_lens_80, color=C["cmb"], lw=2.4)
a2.axhline(D_BB_r_80, color=C["cmb"], lw=2, ls="--")
a2.fill_between(nu, dust(3.7), dust(5.2), color=C["dust"], alpha=0.35, lw=0)
a2.plot(nu, dust(4.4), color=C["dust"], lw=2.4)
a2.fill_between(nu, 1e-6, sync_lim, color=C["sync"], alpha=0.15, lw=0)
a2.plot(nu, sync_lim, color=C["sync"], lw=1.6, ls=":")
a2.set_title(r"Polarisation B-modes, large scales ($\ell = 80$)", fontsize=16)
a2.set_ylim(1e-4, 30)

from matplotlib.ticker import NullFormatter
for ax in (a1, a2):
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(20, 450)
    ax.set_xticks([30, 100, 300]); ax.set_xticklabels(["30", "100", "300"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_ylabel(r"$D_\ell$  [$\mu$K$^2_{\rm CMB}$]", fontsize=15)
    ax.tick_params(labelsize=14)
    for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
a2.set_xlabel("frequency [GHz]", fontsize=15)

# direct labels, placed in empty regions next to each curve
lab = dict(fontsize=14, ha="left", va="center")
a1.text(300, D_TT_3000*1.6, "CMB", color=C["cmb"], **lab)
a1.text(23, 7, "tSZ", color=C["tsz"], **lab)
a1.text(23, 0.85, "kSZ", color=C["ksz"], **lab)
a1.text(110, 300, "CIB", color=C["cib"], **lab)
a1.text(55, 1100, "radio", color=C["radio"], **lab)
a2.text(23, D_BB_lens_80*1.6, "CMB lensing", color=C["cmb"], **lab)
a2.text(118, D_BB_r_80*0.6, "primordial, r = 0.01", color=C["cmb"], **lab)
a2.text(330, 0.15, "dust", color=C["dust"], **lab)
a2.text(23, 6, "synchrotron\n(upper limit)", color=C["sync"], fontsize=13, ha="left", va="center")

fig.savefig(out, dpi=200, facecolor="white")
if "--full" in sys.argv: fig.savefig(out + ".full.png", dpi=200, facecolor="white")

# Shrink for the web: 900 px wide, 64-colour palette
from PIL import Image
im = Image.open(out).convert("RGB")
im = im.resize((900, round(900*im.height/im.width)), Image.LANCZOS)
im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(out, optimize=True)
print(f"D_TT(3000)={D_TT_3000:.1f}  D_BB_lens(80)={D_BB_lens_80:.4f}  D_BB_r=0.01(80)={D_BB_r_80:.5f}")
