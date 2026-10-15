#!/usr/bin/env python3
"""Control-plane latency figures for the paper (Table IV, Fig. 7, Fig. 8).

Every value below is a frame.time_relative timestamp (s) read with tshark from
three packet captures recorded on the core Docker bridge (captures are not
distributed because they contain subscriber identifiers). For each milestone the
first copy of each SIP message seen on the bridge is used. Sessions:
  A = capture 1, B = capture 2, C = capture 3 (frame numbers noted inline).

Usage: python3 generate_plots.py   -> writes fig_kpi_breakdown.pdf and
fig_cdf_latency.pdf next to this script and prints the Table IV statistics.
"""
from pathlib import Path
import statistics as st
import matplotlib
OUT = Path(__file__).parent.resolve()
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

# IMS registration: REGISTER(1) -> 401 -> REGISTER(2) -> 200 OK
REG = {
    "A1": (5.432248, 5.635057, 6.012381, 6.123993),     # frames 947,1174,1561,1689
    "A2": (40.099776, 40.290867, 40.691631, 40.782503), # 5876,6293,6733,6813
    "B1": (7.350575, 7.566239, 7.960052, 8.056460),     # 291,571,770,853
    "B2": (9.267621, 9.476536, 9.842361, 9.976228),     # 1194,1424,1556,1717
    "C1": (20.100743, 20.246630, 20.640303, 20.731796), # 427,694,1001,1088
    "C2": (22.073958, 22.254497, 23.408595, 23.448108), # 1372,1561,1648,1720
}
# Initial call: INVITE -> 180 Ringing
ALERT = {
    "A1": (12.453041, 12.972605),   # 2541 -> 2888
    "A2": (97.823373, 98.361979),   # 12167 -> 12485
    "A3": (163.022085, 163.751708), # 36939 -> 37293
    "B1": (12.674096, 13.161703),   # 2650 -> 2985
    "C1": (27.441869, 31.064118),   # 1876 -> 2228 (INVITE retransmitted at 30.39 s)
}
# Video upgrade: re-INVITE(m=video) -> 183 -> UPDATE -> 200(UPDATE) -> 200(INVITE)
VID = {
    "A1": (108.737856, 108.845322, 108.990993, 109.064134, 113.474063),
    "A2": (169.671036, 169.781861, 169.955838, 170.025896, 173.485797),
    "B1": (16.240156, 16.345317, 16.502505, 16.566792, 19.675678),
    "C1": (39.349855, 39.471592, 39.627758, 39.688323, 43.351249),
}
ms = lambda a, b: (b - a) * 1000

def summary(name, xs):
    q = st.quantiles(xs, n=4, method="inclusive")
    print(f"{name:34s} n={len(xs)} median={st.median(xs):7.1f} IQR={q[0]:.1f}-{q[2]:.1f} "
          f"range={min(xs):.1f}-{max(xs):.1f} mean={st.mean(xs):.1f} sd={st.stdev(xs):.1f}")

reg_total = [ms(t[0], t[3]) for t in REG.values()]
reg_net1 = [ms(t[0], t[1]) for t in REG.values()]
reg_ue = [ms(t[1], t[2]) for t in REG.values()]
reg_net2 = [ms(t[2], t[3]) for t in REG.values()]
alert = [ms(*t) for t in ALERT.values()]
v183 = [ms(t[0], t[1]) for t in VID.values()]
vupd = [ms(t[2], t[3]) for t in VID.values()]
vpre = [ms(t[0], t[3]) for t in VID.values()]
vtot = [ms(t[0], t[4]) for t in VID.values()]
for n, x in [("Registration total", reg_total), ("  REGISTER->401 (network)", reg_net1),
             ("  401->REGISTER (UE interval)", reg_ue), ("  REGISTER->200 (network)", reg_net2),
             ("Alerting INVITE->180", alert), ("Video re-INVITE->183", v183),
             ("Video UPDATE->200", vupd), ("Video precondition phase", vpre),
             ("Video upgrade to 200 OK", vtot)]:
    summary(n, x)
print("UE share of registration (%):", [round(100 * u / t, 1) for u, t in zip(reg_ue, reg_total)])
print("Precondition share of upgrade (%):", [round(100 * p / t, 1) for p, t in zip(vpre, vtot)])

plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Nimbus Roman", "Times New Roman"],
                     "mathtext.fontset": "stix", "pdf.fonttype": 42, "ps.fonttype": 42,
                     "font.size": 7, "axes.linewidth": 0.6})
C_NET, C_UE, C_USER = "#1f77b4", "#ff7f0e", "#bdbdbd"

# ---- Fig. 7 (median/IQR breakdown) and Fig. 8 (empirical CDF) ----
def iqr(xs):
    q = st.quantiles(xs, n=4, method="inclusive"); return q[0], q[2]

rows = [("IMS Reg. (REGISTER$\\rightarrow$401)", reg_net1),
        ("UE AKA interval (401$\\rightarrow$REG.)", reg_ue),
        ("IMS Reg. (REGISTER$\\rightarrow$200)", reg_net2),
        ("Total IMS Registration", reg_total),
        ("VoLTE Call Alerting", alert),
        ("ViLTE re-INVITE$\\rightarrow$183", v183),
        ("ViLTE UPDATE$\\rightarrow$200 OK", vupd),
        ("ViLTE QoS Precondition Phase", vpre)]
med = [st.median(x) for x in [r[1] for r in rows]]
lo = [m - iqr(x)[0] for m, (_, x) in zip(med, rows)]
hi = [iqr(x)[1] - m for m, (_, x) in zip(med, rows)]
fig, ax = plt.subplots(figsize=(3.45, 1.9))
fig.subplots_adjust(left=0.42)
yy = range(len(rows))
bars = ax.barh(list(yy), med, xerr=[lo, hi], capsize=2.5, color="#1f77b4", edgecolor="black",
               alpha=0.85, height=0.65, error_kw={"lw": 0.6})
for i, m in enumerate(med):
    ax.text(m + hi[i] + 12, i, f"{m:.0f}", va="center", fontsize=6)
ax.set_yticks(list(yy)); ax.set_yticklabels([r[0] for r in rows], fontsize=6)
ax.invert_yaxis(); ax.set_xlabel("Latency (ms), median with IQR"); ax.set_xlim(0, 900)
ax.grid(axis="x", lw=0.3, alpha=0.5)
fig.savefig(OUT / "fig_kpi_breakdown.pdf", bbox_inches="tight", pad_inches=0.02); plt.close(fig)

def ecdf(ax, xs, label, style):
    xs = sorted(xs); n = len(xs)
    ys = [(i + 1) / n for i in range(n)]
    mk = style.pop("marker", "o")
    ax.step([xs[0]] + xs, [0] + ys, where="post", label=f"{label} (n={n})", marker=None, **style)
    ax.plot(xs, ys, linestyle="none", marker=mk, ms=3, color=style["color"])
fig, ax = plt.subplots(figsize=(3.45, 1.7))
ecdf(ax, reg_total, "IMS registration", {"color": "#2ca02c", "lw": 1, "marker": "s"})
ecdf(ax, alert, "VoLTE call alerting", {"color": "#1f77b4", "lw": 1, "marker": "o"})
ecdf(ax, vpre, "ViLTE QoS precondition phase", {"color": "#ff7f0e", "lw": 1, "marker": "^"})
ax.set_xscale("log"); ax.set_xlim(250, 9000)
ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.set_xticks([300, 500, 700, 1000, 2000, 4000]); ax.set_xticklabels(["300", "500", "700", "1000", "2000", "4000"])
ax.set_xlabel("Latency (ms, log scale)"); ax.set_ylabel("Empirical CDF"); ax.set_ylim(0, 1.05)
ax.legend(fontsize=5.5, frameon=False, loc="lower right"); ax.grid(lw=0.3, alpha=0.5)
fig.tight_layout(pad=0.2); fig.savefig(OUT / "fig_cdf_latency.pdf"); plt.close(fig)
