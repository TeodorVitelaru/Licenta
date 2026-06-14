"""
Antrenare Gradient Boosting MULTICLASS
"""

import pandas as pd
import numpy as np
import joblib
import time

from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

import warnings
warnings.filterwarnings("ignore")

RANDOM_STATE = 42

print("=" * 90)
print(" GRADIENT BOOSTING MULTICLASS - FINAL VERSION (UPDATED)")
print("=" * 90)

print("\n Loading dataset...")

df = pd.read_csv("../model/dataset_training.csv")
df["target"] = df["final_result"] + 1  # -1,0,1 → 0,1,2

print(f" Dataset: {len(df):,} rows")

# FEATURE ENGINEERING (IDENTIC CU LGBM)
print("\n Feature engineering...")

df = df.sort_values(["match_id", "minute"]).copy()

df["score_momentum"] = df.groupby("match_id")["score_diff"].diff().fillna(0)

df["xg_momentum"] = (
    df.groupby("match_id")["xg_diff"]
    .diff()
    .groupby(df["match_id"])
    .rolling(3, min_periods=1)
    .mean()
    .reset_index(level=0, drop=True)
    .fillna(0)
)

df["pressure_momentum"] = (
    df.groupby("match_id")["pressure_home"]
    .diff()
    .groupby(df["match_id"])
    .rolling(3, min_periods=1)
    .mean()
    .reset_index(level=0, drop=True)
    .fillna(0)
)

df["max_minute"] = df.groupby("match_id")["minute"].transform("max")
df["time_remaining"] = df["max_minute"] - df["minute"]
df["time_remaining_norm"] = df["time_remaining"] / df["max_minute"]

df["is_late_game"] = (df["minute"] > 75).astype(int)
df["is_early_game"] = (df["minute"] < 30).astype(int)
df["is_crunch_time"] = (df["score_diff"].abs() <= 1).astype(int)
df["is_winning"] = (df["score_diff"] > 0).astype(int)

df["score_xg_gap"] = df["score_diff"] - df["xg_diff"]
df["pressure_advantage"] = df["pressure_home"] - df["pressure_away"]

print(" Features added")

feature_cols = [
    'minute', 'timestamp_seconds',
    'score_home', 'score_away', 'score_diff',
    'red_cards_home', 'red_cards_away',
    'yellow_cards_home', 'yellow_cards_away',
    'cards_diff',
    'xg_home', 'xg_away', 'xg_diff',
    'shots_home', 'shots_away',
    'shots_on_target_home', 'shots_on_target_away',
    'passes_home', 'passes_away',
    'pressure_home', 'pressure_away',
    'is_home_team', 'under_pressure', 'counterpress',

    # Momentum
    'score_momentum', 'xg_momentum', 'pressure_momentum',

    # Time
    'time_remaining_norm',
    'is_late_game', 'is_early_game', 'is_crunch_time',

    # Context
    'is_winning',
    'score_xg_gap'
]

X = df[feature_cols]
y = df["target"]

# SPLIT BY MATCH
print("\n Splitting by matches...")

match_ids = df["match_id"].unique()

train_ids, test_ids = train_test_split(
    match_ids,
    test_size=0.2,
    random_state=RANDOM_STATE
)

train_mask = df["match_id"].isin(train_ids)
test_mask = df["match_id"].isin(test_ids)

X_train, X_test = X[train_mask], X[test_mask]
y_train, y_test = y[train_mask], y[test_mask]

print(f"Train: {len(X_train):,} samples")
print(f"Test : {len(X_test):,} samples")

# MODEL (FIXED PARAMETERS)
print("\n Training Gradient Boosting...")

model = GradientBoostingClassifier(
    n_estimators=200,        
    learning_rate=0.05,     
    max_depth=5,           
    subsample=0.8,          
    min_samples_leaf=10,    
    random_state=RANDOM_STATE,
    verbose=2
)

start = time.time()
model.fit(X_train, y_train)
elapsed = time.time() - start

print(f"\n Training completed in {elapsed/60:.2f} minutes")

# EVALUARE
print("\n Evaluation on test set...")

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)

acc = accuracy_score(y_test, y_pred)

print(f"\n Accuracy: {acc:.4f}")

print("\n Classification Report:")
print(classification_report(
    y_test,
    y_pred,
    target_names=["Away Win", "Draw", "Home Win"],
    digits=4
))

print("\n Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
print(cm)

# FEATURE IMPORTANCE
print("\n Top Feature Importance:")

fi = pd.DataFrame({
    "feature": feature_cols,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

print(fi.head(15))

joblib.dump(model, "gb_final_model.pkl")
joblib.dump(feature_cols, "gb_feature_cols.pkl")

print("\n Saved:")
print(" - gb_final_model.pkl")
print(" - gb_feature_cols.pkl")


print("\n" + "=" * 90)
print(" GRADIENT BOOSTING TRAINING COMPLETE")
print("=" * 90)

