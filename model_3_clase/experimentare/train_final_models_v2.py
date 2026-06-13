"""
FINAL MODELS 
=======================================================
Split: by_matches (80/20) with intelligent feature engineering
RandomizedSearchCV: n_iter=12-15 per model
CV: GroupKFold(2)
Features: momentum + time context + match state

"""

import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV, train_test_split, GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import log_loss, f1_score
import pickle
import os
from datetime import datetime
import warnings
from tqdm import tqdm
warnings.filterwarnings('ignore')

DATA_PATH = r"e:\licenta\model\dataset_training.csv"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

def add_feature_engineering(df):
    """
    MOMENTUM + TIME + CONTEXT FEATURES
    """
    print("[FEATURES] Adding momentum + time context features...")

    df = df.sort_values(['match_id', 'minute']).copy()

    # MOMENTUM FEATURES 
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

    # TIME FEATURES
    df['max_minute'] = df.groupby('match_id')['minute'].transform('max')
    df['time_remaining'] = df['max_minute'] - df['minute']
    df['time_remaining_norm'] = df['time_remaining'] / df['max_minute']

    # MATCH CONTEXT FEATURES
    df['is_late_game'] = (df['minute'] > 75).astype(int)
    df['is_early_game'] = (df['minute'] < 30).astype(int)
    df['is_crunch_time'] = (df['score_diff'].abs() <= 1).astype(int)
    df['is_winning'] = (df['score_diff'] > 0).astype(int)

    # INTERACTION FEATURES
    df['score_xg_gap'] = df['score_diff'] - df['xg_diff']

    print(f"Added 9 new features (momentum, time, context)")

    return df

def load_data_by_matches(sample_matches=None):
    """
    Load data, add features, split by matches (80/20).
    Optional: limit matches for faster tuning.
    """
    print("[LOADING] Data from dataset_training.csv...")

    df = pd.read_csv(DATA_PATH)
    print(f"  Full dataset: {len(df):,} rows")

    # ADD FEATURE ENGINEERING
    # df = add_feature_engineering(df)

    # BASE feature columns
    feature_cols = [
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
        # Momentum
        # 'score_momentum', 'xg_momentum', 'pressure_momentum',

        # Time
        # 'time_remaining_norm',
        # 'is_late_game', 'is_early_game', 'is_crunch_time',

        # Context
        # 'is_winning',
        # 'score_xg_gap'
    ]

    df['target'] = df['final_result'] + 1

    # SPLIT BY MATCHES FIRST (80/20)
    # print(f"\n[SPLIT] Splitting by matches (80/20)...")
    # match_ids = df['match_id'].unique()
    # print(f"  Total matches: {len(match_ids)}")

    train_matches, test_matches = joblib.load("fixed_split.pkl")

    # train_matches, test_matches = train_test_split(
    # match_ids, test_size=0.2, random_state=42
    # )
    # joblib.dump((train_matches, test_matches), "fixed_split.pkl")
    print(f"  Train matches: {len(train_matches)}")
    print(f"  Test matches: {len(test_matches)}")

    # OPTIONAL: Limit train matches
    if sample_matches is not None and len(train_matches) > sample_matches:
        print(f"\n[SAMPLE] Limiting to {sample_matches} matches...")
        train_matches = np.random.choice(
            train_matches, sample_matches, replace=False
        )
        test_matches = np.random.choice(
            test_matches, int(sample_matches * 0.3), replace=False)

    train_mask = df['match_id'].isin(train_matches)
    test_mask = df['match_id'].isin(test_matches)

    X_train = df.loc[train_mask, feature_cols]
    y_train = df.loc[train_mask, 'target']
    train_groups = df.loc[train_mask, 'match_id'].values

    X_test = df.loc[test_mask, feature_cols]
    y_test = df.loc[test_mask, 'target']

    print(f"\n[DATA SHAPE]")
    print(
        f"  Train: {len(X_train):,} samples, {len(np.unique(train_groups))} matches")
    print(
        f"  Test:  {len(X_test):,} samples, {len(np.unique(df.loc[test_mask, 'match_id']))} matches")
    print(f"  Features: {len(feature_cols)}")

    # Class distribution
    unique, counts = np.unique(y_train, return_counts=True)
    dist = dict(zip(unique, counts))
    pct = {k: 100*v/len(y_train) for k, v in dist.items()}
    print(f"\n[CLASS DISTRIBUTION]")
    print(f"  Class 0 (Away): {dist.get(0, 0):,} ({pct.get(0, 0):.1f}%)")
    print(f"  Class 1 (Draw): {dist.get(1, 0):,} ({pct.get(1, 0):.1f}%)")
    print(f"  Class 2 (Home): {dist.get(2, 0):,} ({pct.get(2, 0):.1f}%)")

    return X_train, X_test, y_train, y_test, train_groups

def train_model(model_name, param_dist, X_train, X_test, y_train, y_test, train_groups):
    """
    Train model with RandomizedSearchCV.

    - RandomizedSearchCV: sample 12-15 combinations
    - GroupKFold(2): match-aware, fast
    """

    print(f"\n{'='*80}")
    print(f"MODEL: {model_name.upper()}")
    print(f"{'='*80}")

    if model_name == "gradient_boosting":
        estimator = Pipeline([
            ('clf', GradientBoostingClassifier(
                random_state=42,
                n_iter_no_change=10,
                validation_fraction=0.1
            ))
        ])
        n_iter = 12
    elif model_name == "lgbm":
        estimator = Pipeline([
            ('clf', lgb.LGBMClassifier(
                random_state=42,
                verbose=-1,
                n_jobs=1,
                n_estimators=100
            ))
        ])
        n_iter = 15
    elif model_name == "logistic_regression":
        estimator = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(
                random_state=42,
                max_iter=500,
                n_jobs=1
            ))
        ])
        n_iter = 8
    elif model_name == "random_forest":
        estimator = Pipeline([
            ('clf', RandomForestClassifier(
                random_state=42,
                n_jobs=1
            ))
        ])
        n_iter = 10
    else:
        raise ValueError(f"Unknown model: {model_name}")

    print(f"\nRandomizedSearchCV Configuration:")
    print(f"  n_iter: {n_iter}")
    print(f"  CV: GroupKFold(2) ")
    print(f"  Total evaluations: {n_iter} × 2 = {n_iter * 2}")
    print(f"  Scoring: neg_log_loss")

    # RandomizedSearchCV
    print(f"\n[TUNING] Starting RandomizedSearchCV...")
    gkf = GroupKFold(n_splits=2)

    random_search = RandomizedSearchCV(
        estimator=estimator,
        param_distributions=param_dist,
        n_iter=n_iter,
        cv=gkf,
        scoring='neg_log_loss',
        n_jobs=-1,
        verbose=2,
        random_state=42,
        return_train_score=False
    )

    random_search.fit(X_train, y_train, groups=train_groups)

    # Get best model
    best_model = random_search.best_estimator_
    print(f"\n[BEST PARAMS]")
    print(f"  CV Score: {random_search.best_score_:.4f}")
    for param, value in random_search.best_params_.items():
        print(f"  {param}: {value}")

    # RAW MODEL EVALUATION
    y_test_proba = best_model.predict_proba(X_test)

    test_log_loss = log_loss(y_test, y_test_proba, labels=[0, 1, 2])
    test_acc = best_model.score(X_test, y_test)
    test_f1 = f1_score(
        y_test,
        best_model.predict(X_test),
        average='macro',
        zero_division=0
    )

    print(f"\n[TEST METRICS - RAW MODEL]")
    print(f"  Accuracy:  {test_acc:.4f}")
    print(f"  Log-Loss:  {test_log_loss:.4f}")
    print(f"  F1-Macro:  {test_f1:.4f}")

    # UNCERTAINTY (ENTROPY)
    entropy = -np.sum(y_test_proba * np.log(y_test_proba + 1e-9), axis=1)

    print(f"\n[UNCERTAINTY ANALYSIS]")
    print(f"  Mean entropy: {np.mean(entropy):.4f}")
    print(f"  Median entropy: {np.median(entropy):.4f}")
    print(f"  High confidence (<0.5): {(entropy < 0.5).mean():.2%}")
    print(f"  Very uncertain (>1.0): {(entropy > 1.0).mean():.2%}")

    # Save models
    raw_path = os.path.join(
        OUTPUT_DIR, f"{model_name}_with_old_features_500matches.pkl")
    with open(raw_path, 'wb') as f:
        pickle.dump(best_model, f)
    print(f"\n[SAVED] {raw_path}")

    return {
        'model': model_name,
        'best_params': random_search.best_params_,
        'cv_score': random_search.best_score_,
        'test_accuracy': test_acc,
        'test_log_loss': test_log_loss,
        'test_f1': test_f1,
    }

def main():
    print("="*80)
    print("FINAL MODELS - INDUSTRY PRACTICE (SMART ENGINEERING)")
    print("="*80)
    print(f"Split: by_matches (80/20) with feature engineering")
    print(f"Tuning: RandomizedSearchCV (controlled budget)")
    print(f"CV: GroupKFold(2) ")
    print(f"Features: base + momentum + time + context (9 new)")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Load data + features
    print()
    X_train, X_test, y_train, y_test, train_groups = load_data_by_matches(
        sample_matches=500
    )

    # Parameter distributions
    param_distributions = {
        "gradient_boosting": {
            'clf__n_estimators': [100, 150, 200, 300],
            'clf__max_depth': [3, 5, 7, 9],
            'clf__learning_rate': [0.01, 0.05, 0.1],
            'clf__subsample': [0.7, 0.8, 1.0],
            'clf__min_samples_split': [2, 5],
            'clf__min_samples_leaf': [1, 2],
        },
        "lgbm": {
            'clf__num_leaves': [15, 31, 63],
            'clf__max_depth': [5, 7, 9, 11],
            'clf__learning_rate': [0.01, 0.05, 0.1],
            'clf__feature_fraction': [0.7, 0.8, 1.0],
            'clf__bagging_fraction': [0.7, 0.8, 1.0],
            'clf__min_data_in_leaf': [10, 20],
            'clf__n_estimators': [200, 300, 500],
        },
        "logistic_regression": {
            'clf__C': [0.01, 0.1, 1, 10, 100],
            'clf__solver': ['lbfgs', 'saga'],
            'clf__class_weight': [None, 'balanced'],
        }
    }

    # Train all models
    print(f"\n{'='*80}")
    print("TRAINING ALL MODELS")
    print(f"{'='*80}\n")

    results = []
    #  BEST MODELS: LGBM + GB + LR
    model_names = ["lgbm", "gradient_boosting", "logistic_regression"]

    print(f"\nModels to train: {', '.join(model_names)}")

    for model_name in tqdm(model_names, desc="Models"):
        param_dist = param_distributions[model_name]
        result = train_model(
            model_name, param_dist,
            X_train, X_test, y_train, y_test, train_groups
        )
        results.append(result)

    # Summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}\n")

    summary_data = []
    for r in results:
        summary_data.append({
            'Model': r['model'],
            'CV Score': f"{r['cv_score']:.4f}",
            'Test Acc': f"{r['test_accuracy']:.4f}",
            'Log-Loss': f"{r['test_log_loss']:.4f}",
            'F1-Macro': f"{r['test_f1']:.4f}",
        })

    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))

    # Save summary
    summary_path = os.path.join(
        OUTPUT_DIR, "models_summary_with_old_features_500matches.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"\n[SAVED] {summary_path}")

    # Save report
    report_path = os.path.join(
        OUTPUT_DIR, "models_report_with_old_features_500matches.txt")
    with open(report_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("FINAL MODELS REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("METHODOLOGY:\n")
        f.write("  - Split: by_matches (80/20 on match_ids)\n")
        f.write("  - Tuning: RandomizedSearchCV\n")
        f.write("  - CV: GroupKFold(2) \n")
        f.write("  - Features: base + momentum + time + context (9 new)\n")

        for r in results:
            f.write(f"\n{'='*80}\n")
            f.write(f"MODEL: {r['model'].upper()}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"CV Score (neg_log_loss): {r['cv_score']:.4f}\n\n")
            f.write(f"Best Hyperparameters:\n")
            for param, value in r['best_params'].items():
                f.write(f"  {param}: {value}\n")
            f.write(f"\nTest Set Performance (Raw Model):\n")
            f.write(f"  Accuracy: {r['test_accuracy']:.4f}\n")
            f.write(f"  Log-Loss: {r['test_log_loss']:.4f}\n")
            f.write(f"  F1-Macro: {r['test_f1']:.4f}\n")

    print(f"[SAVED] {report_path}")

    print(f"\n{'='*80}")
    print("!! TRAINING COMPLETED SUCCESSFULLY !!")
    print(f"{'='*80}\n")
    print("Output Files:")
    for model_name in model_names:
        print(f"  - {model_name}_with_old_features_500matches.pkl")
    print(f"  - models_summary_with_old_features_500matches.csv")
    print(f"  - final_models_report.txt")

if __name__ == "__main__":
    main()
