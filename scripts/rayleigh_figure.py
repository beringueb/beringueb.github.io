"""Generates static/images/rayleigh_lss.png (run: python scripts/rayleigh_figure.py out.png; needs numpy scipy matplotlib camb).
Rayleigh scattering figure: frequency-dependent last-scattering surface.
Visibility functions computed with CAMB background + Rayleigh opacity
sigma_R = sigma_T [x^4 + 638/243 x^6 + 1626820991/136048896 x^8], x = nu/nu_eff, nu_eff = 3.1e15 Hz,
on neutral hydrogen (1 - x_HII) n_H. Schematic geometry is NOT to scale."""
import sys, numpy as np, camb
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from scipy.integrate import cumulative_trapezoid

out = sys.argv[1]
pars = camb.set_params(H0=67.5, ombh2=0.022, omch2=0.12, As=2.1e-9, ns=0.965, tau=0.054)
res = camb.get_background(pars)
z = np.linspace(400, 2200, 8000)
ev = res.get_background_redshift_evolution(z, ['x_e', 'opacity'])
xe, opT = ev['x_e'], ev['opacity']
eta = res.conformal_time(z)
nu_eff = 3.1e15
xHII = np.minimum(xe, 1.0)
def sig(nu):
    x = nu / nu_eff
    return x**4 + 638/243*x**6 + 1626820991/136048896*x**8
def vis(nu0):
    op = opT + opT/xe*(1-xHII)*sig(nu0*1e9*(1+z))
    tau = cumulative_trapezoid(op, -eta, initial=0)   # z ascending => eta descending
    return op*np.exp(-tau)

freqs = [(150, "#b2182b"), (545, "#8e5ea2"), (857, "#2166ac")]
g0 = vis(150); norm = g0.max()

plt.rcParams.update({"font.family": "serif", "font.size": 16, "mathtext.fontset": "dejavuserif"})
fig = plt.figure(figsize=(6.4, 8.2))

# ---------------- top: geometry (schematic, not to scale) ----------------
ax = fig.add_axes([0.0, 0.395, 1.0, 0.595]); ax.set_aspect("equal"); ax.axis("off")
ax.set_xlim(-1.12, 1.12); ax.set_ylim(-0.20, 1.50)
R = {"low": 1.25, "high": 0.98}
col = {"low": freqs[0][1], "high": freqs[-1][1]}
t1, t2 = 40, 140
for k in R:
    for w, a_ in [(24, .10), (14, .20), (6, .55)]:
        ax.add_patch(Arc((0, 0), 2*R[k], 2*R[k], theta1=t1, theta2=t2, lw=w, color=col[k], alpha=a_, capstyle="butt"))
# frequency labels following the arcs: "low ν" outside the outer arc, "high ν" in the gap between arcs
for k, r, ang in [("low", R["low"] + 0.15, 57), ("high", (R["low"] + R["high"]) / 2, 57)]:
    t = np.radians(ang)
    ax.text(r*np.cos(t), r*np.sin(t), "low ν" if k == "low" else "high ν", color=col[k], fontsize=17,
            ha="center", va="center", rotation=ang-90, rotation_mode="anchor")
# same physical size on both shells, and the lines of sight to its edges
L = 0.56
for k in R:
    y = R[k]
    ax.plot([-L/2, L/2], [y, y], color="k", lw=3.5, solid_capstyle="butt", zorder=5)
    for s_ in (-1, 1):
        ax.plot([0, s_*L/2], [0, y], color=col[k], lw=2, zorder=4)
ax.text(0, R["low"]+0.09, "same physical size", ha="center", va="bottom", fontsize=16)
# angles at the observer (larger angle drawn further out so it also looks larger)
for k, r in [("low", 0.45), ("high", 0.64)]:
    th = np.arctan2(L/2, R[k])
    ax.add_patch(Arc((0, 0), 2*r, 2*r, theta1=90-np.degrees(th), theta2=90+np.degrees(th), lw=2.2, color=col[k]))
    y = r*np.cos(th)
    x_outer = y*(L/2)/R["high"]            # outermost line of sight at this height
    ax.text(x_outer + 0.05, y, r"$\theta_{\rm high}$" if k == "high" else r"$\theta_{\rm low}$",
            color=col[k], ha="left", va="center", fontsize=17)
ax.plot(0, 0, marker="o", ms=11, color="k")
ax.text(0, -0.07, "observer", ha="center", va="top", fontsize=15)
ax.text(-1.09, 1.47, "not to scale", ha="left", va="top", fontsize=12, color="#666", style="italic")

# ---------------- bottom: visibility functions (CAMB) ----------------
ins = fig.add_axes([0.11, 0.07, 0.85, 0.27])
for nu, c in freqs:
    g = vis(nu)/norm
    ins.plot(z, g, color=c, lw=2.4, label=f"{nu} GHz")
    ins.axvline(z[np.argmax(g)], color=c, lw=1.3, ls=":")
ins.set_xlim(1250, 930); ins.set_ylim(0, 1.05)
ins.set_xticks([1200, 1100, 1000]); ins.set_yticks([])
ins.set_xlabel("redshift  (later →)", fontsize=15, labelpad=2)
ins.set_ylabel("last scattering\nprobability", fontsize=13)
ins.tick_params(labelsize=14)
ins.legend(fontsize=13, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3,
           handlelength=1.2, columnspacing=1.0, borderaxespad=0.2)
for s_ in ("top", "right"): ins.spines[s_].set_visible(False)

fig.savefig(out, dpi=200, facecolor="white")

# Shrink for the web: 900 px wide, 64-colour palette (~50 KB)
from PIL import Image
im = Image.open(out).convert("RGB")
im = im.resize((900, round(900 * im.height / im.width)), Image.LANCZOS)
im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(out, optimize=True)
