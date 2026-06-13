"""
RE-ANTRENARE LightGBM FINAL - 33 FEATURES (24 de bază + 9 derivate)
====================================================================
Modelul final documentat în lucrare folosește 24 features de bază + 9 features
noi (momentum, context temporal, context de joc).

Acest script reproduce modelul final exact pe cele 33 de features:

"""

import os
import shutil
import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from sklearn.calibration import calibration_curve

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = r"e:\licenta\model\dataset_training.csv"
SPLIT_PATH = os.path.join(HERE, "fixed_split.pkl")
MODEL_PATH = os.path.join(HERE, "lgbm_final_model.pkl")
BACKUP_PATH = os.path.join(HERE, "lgbm_final_model_35feat_backup.pkl")

BASE_FEATURES = [
    'minute', 'timestamp_seconds',
    'score_home', 'score_away', 'score_diff',
    'red_cards_home', 'red_cards_away',
    'yellow_cards_home', 'yellow_cards_away', 'cards_diff',
    'xg_home', 'xg_away', 'xg_diff',
    'shots_home', 'shots_away',
    'shots_on_target_home', 'shots_on_target_away',
    'passes_home', 'passes_away',
    'pressure_home', 'pressure_away',
    'is_home_team', 'under_pressure', 'counterpress',
]

NEW_FEATURES = [
    'score_momentum', 'xg_momentum', 'pressure_momentum',
    'time_remaining_norm',
    'is_late_game', 'is_early_game', 'is_crunch_time', 'is_winning',
    'score_xg_gap',
]

FEATURE_COLS = BASE_FEATURES + NEW_FEATURES

LGBM_PARAMS = dict(
    num_leaves=15,
    max_depth=5,
    learning_rate=0.01,
    n_estimators=500,
    feature_fraction=1.0,
    bagging_fraction=0.8,
    min_data_in_leaf=20,
    random_state=42,
    n_jobs=-1,
    verbose=-1,
)

def add_feature_engineering(df):
    """Cele 9 features noi"""
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
        brier_score_loss((y == i).astype(int), proba[:, i]) for i in range(3)
    ])

def calibration_error(y, proba):
    errors = []
    for i in range(3):
        pt, pp = calibration_curve((y == i).astype(int), proba[:, i], n_bins=10)
        errors.append(np.mean(np.abs(pt - pp)))
    return np.mean(errors)

def main():
    print("=" * 70)
    print("RE-ANTRENARE LightGBM FINAL pe 33 features")
    print("=" * 70)

    print("\n[1/5] Incarc split fix pe meciuri...")
    train_matches, test_matches = joblib.load(SPLIT_PATH)
    print(f"  Train matches: {len(train_matches)} | Test matches: {len(test_matches)}")

    print("\n[2/5] Incarc dataset (doar coloanele numerice necesare)...")
    usecols = ['match_id'] + [c for c in BASE_FEATURES if c != 'minute'] + \
        ['minute', 'final_result']
    usecols = sorted(set(usecols))
    df = pd.read_csv(DATA_PATH, usecols=usecols)
    print(f"  Rânduri: {len(df):,} | coloane: {len(df.columns)}")

    print("\n[3/5] Feature engineering (cele 9 features noi)...")
    df = add_feature_engineering(df)
    df['target'] = df['final_result'] + 1

    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise RuntimeError(f"Lipsesc coloane: {missing}")
    print(f"  Total features model: {len(FEATURE_COLS)}")

    train_mask = df['match_id'].isin(train_matches)
    test_mask = df['match_id'].isin(test_matches)

    X_train = df.loc[train_mask, FEATURE_COLS]
    y_train = df.loc[train_mask, 'target']
    X_test = df.loc[test_mask, FEATURE_COLS]
    y_test = df.loc[test_mask, 'target']
    print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")

    print("\n[4/5] Antrenez LGBMClassifier (Pipeline, fără scaler)...")
    pipeline = Pipeline([('clf', lgb.LGBMClassifier(**LGBM_PARAMS))])
    pipeline.fit(X_train, y_train)
    print("Antrenare completă")

    proba = pipeline.predict_proba(X_test)
    pred = pipeline.predict(X_test)
    metrics = {
        'accuracy': accuracy_score(y_test, pred),
        'log_loss': log_loss(y_test, proba, labels=[0, 1, 2]),
        'rps': rps(y_test.values, proba),
        'brier': brier(y_test.values, proba),
        'calibration_error': calibration_error(y_test.values, proba),
    }
    print("\n[METRICI TEST - 33 features]")
    for k, v in metrics.items():
        print(f"  {k:18s}: {v:.4f}")

    print("\n[5/5] Salvez modelul...")
    if os.path.exists(MODEL_PATH) and not os.path.exists(BACKUP_PATH):
        shutil.copy2(MODEL_PATH, BACKUP_PATH)
        print(f"  Backup model vechi (35 feat) -> {os.path.basename(BACKUP_PATH)}")
    joblib.dump(pipeline, MODEL_PATH)
    clf = pipeline.steps[-1][1]
    print(f" Salvat {os.path.basename(MODEL_PATH)} "
          f"(n_features={clf.n_features_in_})")
    print(f"  feature_name_: {list(clf.feature_name_)}")
    print("\nDONE")


if __name__ == "__main__":
    main()
