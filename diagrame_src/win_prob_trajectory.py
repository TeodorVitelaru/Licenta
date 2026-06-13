"""
Genereaza figura 'win_prob_trajectory.png' - exemplu de traiectorie
probabilistica produsa de model de-a lungul unui meci.

Traiectoria reproduce dinamica meciului real CFR 1907 Cluj - Farul
Constanta (1-2), folosit si in capitolul aplicatiei (figurile descriere*),
pentru consistenta cu restul lucrarii:
  - min 15: gol CFR (1-0)  -> creste P(Home Win)
  - min 50: gol Farul (1-1) -> echilibrare
  - min 62: gol Farul (1-2) -> Farul preia controlul (game changer)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

# Anchor states: (minut, P_home, P_draw, P_away)
# Salturile bruste la goluri sunt redate prin doua puncte la acelasi minut.
anchors = [
    (0,    0.50, 0.28, 0.22),
    (14,   0.52, 0.27, 0.21),
    (15,   0.636, 0.206, 0.158),   # GOL CFR 1-0
    (32,   0.61, 0.22, 0.17),
    (45,   0.57, 0.23, 0.20),
    (49,   0.55, 0.24, 0.21),
    (50,   0.42, 0.30, 0.28),      # GOL Farul 1-1
    (60,   0.38, 0.27, 0.35),
    (62,   0.142, 0.238, 0.62),    # GOL Farul 1-2 (game changer)
    (75,   0.09, 0.18, 0.73),
    (90,   0.04, 0.20, 0.76),
]

anchors = np.array(anchors, dtype=float)
am = anchors[:, 0].copy()
# Decalaj infim pentru a crea salturi verticale la golurile din min 15/50/62
for i in range(1, len(am)):
    if am[i] <= am[i - 1]:
        am[i] = am[i - 1] + 1e-3

# Grila fina de "evenimente" pe parcursul meciului
minutes = np.linspace(0, 90, 400)
p_home = np.interp(minutes, am, anchors[:, 1])
p_draw = np.interp(minutes, am, anchors[:, 2])
p_away = np.interp(minutes, am, anchors[:, 3])

# Renormalizare pentru a garanta suma = 1 in fiecare punct
total = p_home + p_draw + p_away
p_home, p_draw, p_away = p_home / total, p_draw / total, p_away / total

C_HOME = "#2e7d32"
C_DRAW = "#f9a825"
C_AWAY = "#1565c0"

plt.rcParams.update({"font.size": 12, "font.family": "DejaVu Sans"})
fig, ax = plt.subplots(figsize=(10, 5.2))

ax.plot(minutes, p_home, color=C_HOME, lw=2.4, label="Victorie gazda")
ax.plot(minutes, p_draw, color=C_DRAW, lw=2.4, label="Egal")
ax.plot(minutes, p_away, color=C_AWAY, lw=2.4, label="Victorie oaspeti")

# Marcarea golurilor
goals = [
    (15, "Gol gazda (1-0)"),
    (50, "Gol oaspeti (1-1)"),
    (62, "Gol oaspeti (1-2)"),
]
for gm, glabel in goals:
    ax.axvline(gm, color="#b0b0b0", ls="--", lw=1.1, zorder=0)
    ax.annotate(
        glabel,
        xy=(gm, 1.005), xycoords=("data", "axes fraction"),
        ha="center", va="bottom", fontsize=9.5, color="#444444",
        rotation=0,
    )

ax.set_xlim(0, 90)
ax.set_ylim(0, 1)
ax.set_xlabel("Minut de joc (eveniment cu eveniment)")
ax.set_ylabel("Probabilitate estimata")
ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
ax.set_xticks(range(0, 91, 15))
ax.grid(True, alpha=0.25, ls=":")
ax.legend(loc="center left", framealpha=0.9, fontsize=10.5)

fig.tight_layout()
out = "win_prob_trajectory.png"
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"Saved {out}")
