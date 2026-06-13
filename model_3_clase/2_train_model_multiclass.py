"""
Antrenarea modelului MULTICLASS pentru 3 rezultate posibile

"""
import time
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import warnings
from tqdm import tqdm
warnings.filterwarnings('ignore')

RANDOM_STATE = 42

print("=" * 100)
print(" MODEL MULTICLASS - 3 REZULTATE POSIBILE")
print("=" * 100)

print("\n incarcare dataset_training.csv")
df = pd.read_csv("../model/dataset_training.csv")
print(f" Dataset inccrcat: {len(df):,} evenimente")
print(f"   Meciuri: {df['match_id'].nunique()}")

df['target_multiclass'] = df['final_result'] + 1

print(f"\n   Distributie clase (per meci):")
unique_results = df.groupby('match_id')['target_multiclass'].first()
print(f"     0 (Victorie Oaspeti): {(unique_results == 0).sum()} meciuri")
print(f"     1 (Egal):            {(unique_results == 1).sum()} meciuri")
print(f"     2 (Victorie Gazda):  {(unique_results == 2).sum()} meciuri")

# FEATURES
feature_cols = [
    'minute',
    'timestamp_seconds',
    'score_home',
    'score_away',
    'score_diff',
    'red_cards_home',
    'red_cards_away',
    'yellow_cards_home',
    'yellow_cards_away',
    'cards_diff',
    'xg_home',
    'xg_away',
    'xg_diff',
    'shots_home',
    'shots_away',
    'shots_on_target_home',
    'shots_on_target_away',
    'passes_home',
    'passes_away',
    'pressure_home',
    'pressure_away',
    'is_home_team',
    'under_pressure',
    'counterpress'
]

X = df[feature_cols].copy()
y = df['target_multiclass'].copy()

print(f"\n   Features: {X.shape[1]}")
print(f"   Total evenimente: {len(X):,}")

# SPLIT pe MECIURI
print(f"\nSplit train/test pe meciuri...")
match_ids = df['match_id'].unique()
train_matches, test_matches = train_test_split(
    match_ids,
    test_size=0.2,
    random_state=RANDOM_STATE
)

train_mask = df['match_id'].isin(train_matches)
test_mask = df['match_id'].isin(test_matches)

X_train = X[train_mask]
X_test = X[test_mask]
y_train = y[train_mask]
y_test = y[test_mask]

print(
    f"   Train: {len(X_train):,} evenimente din {len(train_matches)} meciuri")
print(f"   Test:  {len(X_test):,} evenimente din {len(test_matches)} meciuri")

# NORMALIZARE
print(f"\n Normalizare features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ANTRENARE GRADIENT BOOSTING MULTICLASS
print(f"\n Antrenare Gradient Boosting Classifier ...")
print(f"   n_estimators: 50 ")
print(f"   max_depth: 5")
print(f"   learning_rate: 0.1")

model = GradientBoostingClassifier(
    n_estimators=50,
    max_depth=5,
    learning_rate=0.1,
    random_state=RANDOM_STATE,
    verbose=2 
)

print(f"\n Incepe antrenarea...")
start_time = time.time()

model.fit(X_train_scaled, y_train)

elapsed_time = time.time() - start_time
print(f"\n Model antrenat cu succes în {elapsed_time/60:.1f} minute!")

# EVALUARE
print(f"\n Evaluare pe test set...")
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)

accuracy = accuracy_score(y_test, y_pred)
print(f"\n Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

print(f"\n Classification Report:")
target_names = ['Victorie Oaspeti', 'Egal', 'Victorie Gazda']
print(classification_report(y_test, y_pred, target_names=target_names, digits=4))

print(f"\n Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
print(f"              Predicted:")
print(f"              Away  Draw  Home")
print(f"   Away     {cm[0,0]:7d} {cm[0,1]:5d} {cm[0,2]:5d}")
print(f"Actual Draw     {cm[1,0]:7d} {cm[1,1]:5d} {cm[1,2]:5d}")
print(f"   Home     {cm[2,0]:7d} {cm[2,1]:5d} {cm[2,2]:5d}")

# IMPORTANTA FEATURES
print(f"\n Top 10 Features Importante:")
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(10).iterrows():
    print(f"   {row['feature']:25s}: {row['importance']:.4f}")

# SALVARE MODEL
print(f"\n Salvare model si rezultate...")
joblib.dump(model, "win_probability_model_3class.pkl")
joblib.dump(scaler, "scaler_3class.pkl")
joblib.dump(feature_cols, "feature_cols.pkl")

# Salveaza test matches pentru evaluare
joblib.dump(test_matches, "test_matches.pkl")

print(f"\n" + "=" * 100)
print(" ANTRENARE COMPLETA!")
print("=" * 100)
print(f"\nModelul poate prezice 3 probabilități simultan:")
