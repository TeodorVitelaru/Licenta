import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import brier_score_loss, accuracy_score, log_loss
from sklearn.calibration import calibration_curve
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# =========================
# LOAD MODELS
# =========================
print("\n[LOADING MODELS]")

gb_model = joblib.load("gb_final_model.pkl")
gb_scaler = joblib.load("scaler_3class.pkl")
gb_features = joblib.load("gb_feature_cols.pkl")

lgbm_model = joblib.load("./experimentare/lgbm_final_model.pkl")

print("✓ Models loaded")

# =========================
# FEATURE ENGINEERING (LGBM)
# =========================


def add_features(df):
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
    df['pressure_advantage'] = df['pressure_home'] - df['pressure_away']

    return df


# =========================
# LOAD DATA
# =========================
print("\n[LOADING DATA]")

df = pd.read_csv("../model/dataset_training.csv")
df['target'] = df['final_result'] + 1

# Split identic
match_ids = df['match_id'].unique()
_, test_matches = train_test_split(match_ids, test_size=0.2, random_state=42)

df_test = df[df['match_id'].isin(test_matches)].copy()

# LGBM features
df_test_lgbm = add_features(df_test)
df_test = add_features(df_test)

lgbm_features = [
    'minute', 'timestamp_seconds', 'score_home', 'score_away', 'score_diff',
    'red_cards_home', 'red_cards_away', 'yellow_cards_home', 'yellow_cards_away', 'cards_diff',
    'xg_home', 'xg_away', 'xg_diff', 'shots_home', 'shots_away',
    'shots_on_target_home', 'shots_on_target_away', 'passes_home', 'passes_away',
    'pressure_home', 'pressure_away', 'is_home_team', 'under_pressure', 'counterpress',
    'score_momentum', 'xg_momentum', 'pressure_momentum',
    'time_remaining', 'time_remaining_norm',
    'is_late_game', 'is_early_game', 'is_crunch_time', 'is_winning',
    'score_xg_gap', 'pressure_advantage'
]

X_gb = df_test[gb_features]

X_lgbm = df_test_lgbm[lgbm_features]

y = df_test['target'].values

# =========================
# PREDICT
# =========================
gb_proba = gb_model.predict_proba(X_gb)
gb_pred = gb_model.predict(X_gb)

lgbm_proba = lgbm_model.predict_proba(X_lgbm)
lgbm_pred = lgbm_model.predict(X_lgbm)

# =========================
# METRICS
# =========================


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
    return np.mean(np.sum((pred_cum - y_true_cum)**2, axis=1) / 2)


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


# Compute
results = []

for name, pred, proba in [
    ("Gradient Boosting", gb_pred, gb_proba),
    ("LightGBM", lgbm_pred, lgbm_proba)
]:
    results.append({
        "model": name,
        "accuracy": accuracy_score(y, pred),
        "logloss": log_loss(y, proba),
        "rps": rps(y, proba),
        "brier": brier(y, proba),
        "calibration": calibration_error(y, proba)
    })

df_results = pd.DataFrame(results)
print("\n=== RESULTS ===")
print(df_results)

# =========================
# BAR CHART COMPARISON
# =========================
metrics = ["accuracy", "logloss", "rps", "brier", "calibration"]

for metric in metrics:
    plt.figure()
    plt.bar(df_results["model"], df_results[metric])
    plt.title(metric.upper())
    plt.grid()
    plt.savefig(f"compare_{metric}.png")

# =========================
# CALIBRATION CURVES COMPARISON
# =========================
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

for i, label in enumerate(["Away", "Draw", "Home"]):
    ax = axes[i]

    for name, proba in [
        ("GB", gb_proba),
        ("LGBM", lgbm_proba)
    ]:
        pt, pp = calibration_curve(
            (y == i).astype(int), proba[:, i], n_bins=10)
        ax.plot(pp, pt, marker='o', label=name)

    ax.plot([0, 1], [0, 1], 'k--')
    ax.set_title(label)
    ax.legend()
    ax.grid()

plt.savefig("compare_calibration.png")

print("\n✓ Charts saved:")
print(" - compare_accuracy2.png")
print(" - compare_logloss2.png")
print(" - compare_rps2.png")
print(" - compare_brier2.png")
print(" - compare_calibration2.png")
