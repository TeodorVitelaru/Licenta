"""
COMPARATIE EXPERIMENTE - evalueaza toate modelele salvate din experimentare/
pe acelasi set de test (held-out), folosind aceleasi metrici ca in
lgbm_gb_comparatie.py: accuracy, logloss, rps, brier, calibration.

Modele comparate (18): {lgbm|gradient_boosting|logistic_regression}
                       x {old|new} features x {100|200|500} matches.

Setul de test este comun pentru toate modelele (test_matches din fixed_split.pkl),
deci comparatia este corecta si fara leakage (antrenarea a folosit doar meciuri
din train, esantionate).
"""

import os
import pickle
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from sklearn.calibration import calibration_curve

warnings.filterwarnings('ignore')

# PATHS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH_CANDIDATES = [
    r"e:\licenta\model\dataset_training.csv",
    os.path.join(SCRIPT_DIR, "..", "..", "model", "dataset_training.csv"),
    os.path.join(SCRIPT_DIR, "..", "model", "dataset_training.csv"),
]

FIXED_SPLIT_PATH = os.path.join(SCRIPT_DIR, "fixed_split.pkl")

MODELS = ["lgbm", "gradient_boosting", "logistic_regression"]
FEATURE_SETS = ["old", "new"]
MATCH_SIZES = [100, 200, 500]

def add_feature_engineering(df):
    """Adauga momentum + time + context features (cele 9 din modelele 'new')."""
    df = df.sort_values(['match_id', 'minute']).copy()

    df['score_momentum'] = df.groupby(
        'match_id')['score_diff'].diff().fillna(0)
    df['xg_momentum'] = (
        df.groupby('match_id')['xg_diff']
        .diff()
        .groupby(df['match_id'])
        .rolling(3, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
        .fillna(0)
    )
    df['pressure_momentum'] = (
        df.groupby('match_id')['pressure_home']
        .diff()
        .groupby(df['match_id'])
        .rolling(3, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
        .fillna(0)
    )

    df['max_minute'] = df.groupby('match_id')['minute'].transform('max')
    df['time_remaining'] = df['max_minute'] - df['minute']
    df['time_remaining_norm'] = df['time_remaining'] / df['max_minute']

    df['is_late_game'] = (df['minute'] > 75).astype(int)
    df['is_early_game'] = (df['minute'] < 30).astype(int)
    df['is_crunch_time'] = (df['score_diff'].abs() <= 1).astype(int)
    df['is_winning'] = (df['score_diff'] > 0).astype(int)

    df['score_xg_gap'] = df['score_diff'] - df['xg_diff']

    return df

# METRICI
def rps(y_true, proba):
    y_true_cum = np.zeros((len(y_true), 3))
    for i, label in enumerate(y_true):
        if label == 0:
            y_true_cum[i] = [1, 1, 1]
        elif label == 1:
            y_true_cum[i] = [0, 1, 1]
        else:
            y_true_cum[i] = [0, 0, 1]

    pred_cum = np.cumsum(proba, axis=1)
    return np.mean(np.sum((pred_cum - y_true_cum) ** 2, axis=1) / 2)

def brier(y, proba):
    return np.mean([
        brier_score_loss((y == i).astype(int), proba[:, i])
        for i in range(3)
    ])

def calibration_error(y, proba):
    errors = []
    for i in range(3):
        pt, pp = calibration_curve(
            (y == i).astype(int), proba[:, i], n_bins=10)
        errors.append(np.mean(np.abs(pt - pp)))
    return np.mean(errors)

# HELPERS
def resolve_data_path():
    for path in DATA_PATH_CANDIDATES:
        if os.path.exists(path):
            return os.path.abspath(path)
    raise FileNotFoundError(
        "Nu am gasit dataset_training.csv. Cautat in:\n  " +
        "\n  ".join(os.path.abspath(p) for p in DATA_PATH_CANDIDATES)
    )

def model_filename(model, feature_set, matches):
    return f"{model}_with_{feature_set}_features_{matches}matches.pkl"

def get_feature_names(model):
    """Extrage exact coloanele cu care a fost antrenat modelul."""
    fn = getattr(model, "feature_names_in_", None)
    if fn is None:
        raise ValueError("Modelul nu expune feature_names_in_")
    return [str(c) for c in fn]

def main():
    print("=" * 80)
    print("COMPARATIE EXPERIMENTE - 18 modele pe set de test comun")
    print("=" * 80)

    # ---- Load data ----
    data_path = resolve_data_path()
    print(f"\n[LOADING DATA] {data_path}")
    df = pd.read_csv(data_path)
    df['target'] = df['final_result'] + 1
    print(f"  Total randuri: {len(df):,}")

    # Common test set din fixed_split.pkl
    print(f"\n[SPLIT] {FIXED_SPLIT_PATH}")
    train_matches, test_matches = joblib_load(FIXED_SPLIT_PATH)
    print(f"  Train matches: {len(train_matches)} | Test matches: {len(test_matches)}")

    df_test = df[df['match_id'].isin(test_matches)].copy()
    df_test = add_feature_engineering(df_test)
    y = df_test['target'].values
    print(f"  Test randuri: {len(df_test):,}")

    # Evaluare per model
    print("\n[EVALUARE]")
    results = []
    for feature_set in FEATURE_SETS:
        for matches in MATCH_SIZES:
            for model_name in MODELS:
                fname = model_filename(model_name, feature_set, matches)
                fpath = os.path.join(SCRIPT_DIR, fname)
                if not os.path.exists(fpath):
                    print(f"  [SKIP] lipseste: {fname}")
                    continue

                with open(fpath, 'rb') as f:
                    model = pickle.load(f)

                feats = get_feature_names(model)
                X = df_test[feats]

                proba = model.predict_proba(X)
                pred = model.predict(X)

                results.append({
                    "features": feature_set,
                    "matches": matches,
                    "model": model_name,
                    "accuracy": accuracy_score(y, pred),
                    "logloss": log_loss(y, proba, labels=[0, 1, 2]),
                    "rps": rps(y, proba),
                    "brier": brier(y, proba),
                    "calibration": calibration_error(y, proba),
                })
                print(f"  [OK] {fname}")

    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(
        ["features", "matches", "model"]).reset_index(drop=True)

    print("\n" + "=" * 80)
    print("=== REZULTATE ===")
    print("=" * 80)
    with pd.option_context('display.max_rows', None,
                           'display.width', 200,
                           'display.float_format', lambda v: f"{v:.4f}"):
        print(df_results.to_string(index=False))

    # Save
    csv_path = os.path.join(SCRIPT_DIR, "comparatie_experimente.csv")
    df_results.to_csv(csv_path, index=False)
    print(f"\n[SAVED] {csv_path}")

    # Charts
    save_charts(df_results)

    return df_results

def joblib_load(path):
    import joblib
    return joblib.load(path)

def save_charts(df_results):
    """Cate un grafic bar pe fiecare metrica (config pe axa X)."""
    metrics = ["accuracy", "logloss", "rps", "brier", "calibration"]
    df = df_results.copy()
    df['config'] = (df['features'] + "_" +
                    df['matches'].astype(str) + "m_" + df['model'])

    for metric in metrics:
        plt.figure(figsize=(14, 6))
        plt.bar(df['config'], df[metric])
        plt.title(metric.upper())
        plt.xticks(rotation=90)
        plt.grid(axis='y')
        plt.tight_layout()
        out = os.path.join(SCRIPT_DIR, f"comparatie_{metric}.png")
        plt.savefig(out)
        plt.close()

    print("\n[SAVED] grafice: comparatie_{accuracy,logloss,rps,brier,calibration}.png")

if __name__ == "__main__":
    main()
