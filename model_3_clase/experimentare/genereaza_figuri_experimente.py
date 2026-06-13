"""
Genereaza figurile pentru capitolul de experimentare, pe baza rezultatelor
deja calculate in comparatie_experimente.csv.

Figuri generate:
  1. rps_vs_matches.png          - RPS (Y) vs volum date (X), o linie per model x feature-set
  2. calibration_vs_matches.png  - ECE (Y) vs volum date (X), cu linie orizontala la 0.05
  3. comparatie_metrici_500.png  - bar chart comparativ pentru toate cele 18 configuratii
                                    (un panou per metrica)
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "comparatie_experimente.csv")

MATCH_SIZES = [100, 200, 500]
MODELS = ["lgbm", "gradient_boosting", "logistic_regression"]
MODEL_LABELS = {
    "lgbm": "LGBM",
    "gradient_boosting": "Gradient Boosting",
    "logistic_regression": "Logistic Regression",
}
MODEL_COLORS = {
    "lgbm": "tab:blue",
    "gradient_boosting": "tab:orange",
    "logistic_regression": "tab:green",
}
MODEL_MARKERS = {
    "lgbm": "o",
    "gradient_boosting": "s",
    "logistic_regression": "^",
}

def line_vs_matches(df, metric, ylabel, title, out_name, hline=None):
    """Linie per (model x feature-set): old = dashed, new = solid."""
    plt.figure(figsize=(9, 6))

    for model in MODELS:
        for feat, style in [("old", "--"), ("new", "-")]:
            sub = df[(df["model"] == model) & (df["features"] == feat)]
            sub = sub.set_index("matches").reindex(MATCH_SIZES)
            label = f"{MODEL_LABELS[model]} ({feat})"
            plt.plot(
                MATCH_SIZES, sub[metric].values,
                marker=MODEL_MARKERS[model], linestyle=style,
                color=MODEL_COLORS[model], label=label,
            )

    if hline is not None:
        plt.axhline(hline, color="red", linestyle=":", linewidth=1.5,
                    label=f"prag {hline}")

    plt.xlabel("Numar de meciuri (volum date)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(MATCH_SIZES)
    plt.grid(True, alpha=0.4)
    plt.legend(fontsize=8)
    plt.tight_layout()

    out = os.path.join(SCRIPT_DIR, out_name)
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"[SAVED] {out}")

def bar_all_configs(df, out_name):
    """Bar chart comparativ pentru toate cele 18 configuratii (un panou per metrica)."""
    metrics = [
        ("accuracy", "Accuracy (mai mare = mai bine)"),
        ("logloss", "Log-Loss (mai mic = mai bine)"),
        ("rps", "RPS (mai mic = mai bine)"),
        ("brier", "Brier (mai mic = mai bine)"),
        ("calibration", "Calibration/ECE (mai mic = mai bine)"),
    ]

    d = df.copy()
    d["config"] = (d["features"] + "_" + d["matches"].astype(str) +
                   "m_" + d["model"])
    d = d.sort_values(["features", "matches", "model"]).reset_index(drop=True)

    colors = [MODEL_COLORS[m] for m in d["model"]]

    fig, axes = plt.subplots(len(metrics), 1, figsize=(14, 22))
    for ax, (metric, title) in zip(axes, metrics):
        ax.bar(d["config"], d[metric], color=colors)
        ax.set_title(title, fontsize=12)
        ax.set_ylabel(metric)
        ax.grid(axis="y", alpha=0.4)
        ax.tick_params(axis="x", rotation=90)
        if metric == "calibration":
            ax.axhline(0.05, color="red", linestyle=":", linewidth=1.5)

    fig.suptitle("Comparatie metrici - toate cele 18 configuratii",
                 fontsize=15, y=1.0)
    fig.tight_layout()

    out = os.path.join(SCRIPT_DIR, out_name)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[SAVED] {out}")

def main():
    df = pd.read_csv(CSV_PATH)

    line_vs_matches(
        df, metric="rps", ylabel="RPS (Ranked Probability Score)",
        title="RPS vs volum de date (per model)",
        out_name="rps_vs_matches.png",
    )

    line_vs_matches(
        df, metric="calibration", ylabel="ECE (Expected Calibration Error)",
        title="Calibrare (ECE) vs volum de date (per model)",
        out_name="calibration_vs_matches.png",
        hline=0.05,
    )

    bar_all_configs(df, out_name="comparatie_metrici_500.png")

    print("\nGata. 3 figuri generate.")

if __name__ == "__main__":
    main()
