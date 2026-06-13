"""
RANDOM FOREST - Model experimental pentru comparație
Antrenarea modelului MULTICLASS pentru 3 rezultate posibile

Input: dataset_training.csv (din folderul model original)
Output: random_forest_3class.pkl, scaler_random_forest.pkl, feature_cols.pkl

Target: 0 = Victorie Oaspeți, 1 = Egal, 2 = Victorie Gazdă
"""
import time
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import warnings
from tqdm import tqdm
warnings.filterwarnings('ignore')

RANDOM_STATE = 42

print("=" * 100)
print(" MODEL MULTICLASS - RANDOM FOREST (3 REZULTATE POSIBILE)")
print("=" * 100)

print("\n Încărcare dataset_training.csv din folderul original...")
df = pd.read_csv("../../model/dataset_training.csv")
print(f"✓ Dataset încărcat: {len(df):,} evenimente")
print(f"   Meciuri: {df['match_id'].nunique()}")

# === TARGET MULTICLASS ===
print("\n Pregătire target multiclass...")

# Convertim final_result (-1, 0, 1) în (0, 1, 2) pentru sklearn
# -1 (away wins) → 0
#  0 (draw)      → 1
#  1 (home wins) → 2
df['target_multiclass'] = df['final_result'] + 1

print(f"\n   Distribuție clase (per meci):")
unique_results = df.groupby('match_id')['target_multiclass'].first()
print(f"     0 (Victorie Oaspeți): {(unique_results == 0).sum()} meciuri")
print(f"     1 (Egal):            {(unique_results == 1).sum()} meciuri")
print(f"     2 (Victorie Gazdă):  {(unique_results == 2).sum()} meciuri")

# === FEATURES ===
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

# === SPLIT pe MECIURI ===
print(f"\n Split train/test pe meciuri...")
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

# === NORMALIZARE (Random Forest nu o necesită, dar o facem pentru consistență) ===
print(f"\n Salvare date fără normalizare (Random Forest nu o necesită)...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# === ANTRENARE RANDOM FOREST MULTICLASS ===
print(f"\n Antrenare Random Forest Classifier (Multiclass)...")
print(f"   n_estimators: 100")
print(f"   max_depth: 10")
print(f"   min_samples_split: 5")
print(f"   n_jobs: -1 (parallelizat pe toate CPU cores)")
print(f"\n Durata estimată: 5-10 minute...")

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    random_state=RANDOM_STATE,
    n_jobs=-1,  # Parallelizare pe toate cores
    verbose=1
)

print(f"\n🔥 Începe antrenarea...")
start_time = time.time()

model.fit(X_train_scaled, y_train)

elapsed_time = time.time() - start_time
print(f"\n Model antrenat cu succes în {elapsed_time/60:.1f} minute!")

# === EVALUARE ===
print(f"\n Evaluare pe test set...")
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)

accuracy = accuracy_score(y_test, y_pred)
print(f"\n Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

print(f"\n Classification Report:")
target_names = ['Victorie Oaspeți', 'Egal', 'Victorie Gazdă']
print(classification_report(y_test, y_pred, target_names=target_names, digits=4))

print(f"\n Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
print(f"              Predicted:")
print(f"              Away  Draw  Home")
print(f"   Away     {cm[0,0]:7d} {cm[0,1]:5d} {cm[0,2]:5d}")
print(f"Actual Draw     {cm[1,0]:7d} {cm[1,1]:5d} {cm[1,2]:5d}")
print(f"   Home     {cm[2,0]:7d} {cm[2,1]:5d} {cm[2,2]:5d}")

# === IMPORTANȚA FEATURES ===
print(f"\n Top 10 Features Importante:")
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(10).iterrows():
    print(f"   {row['feature']:25s}: {row['importance']:.4f}")

# === SALVARE MODEL ===
print(f"\n Salvare model și rezultate...")
joblib.dump(model, "random_forest_3class.pkl")
joblib.dump(scaler, "scaler_random_forest.pkl")
joblib.dump(feature_cols, "feature_cols.pkl")

# Salvează și test matches pentru evaluare
joblib.dump(test_matches, "test_matches.pkl")

print(f"\n Fișiere salvate:")
print(f"   - random_forest_3class.pkl")
print(f"   - scaler_random_forest.pkl")
print(f"   - feature_cols.pkl")
print(f"   - test_matches.pkl")

print(f"\n" + "=" * 100)
print("✅ ANTRENARE RANDOM FOREST COMPLETĂ!")
print("=" * 100)
print(f"\nModelul Random Forest pentru comparație experimentală")
print(f"   Model bazat pe arbori de decizie ensemble")
print(f"   Viteză: RAPIDĂ (parallelizată pe CPU cores)")
print(f"   Performanță: de obicei bună, dar mai puțin stabilă decât Gradient Boosting")
print(f"\n🔬 Pentru analiza comparativă:")
print(f"   1. Rulează scriptul 5_evaluate_model_rigorous.py din directorul parent")
print(f"   2. Compară RPS, Brier Score și calibration curves")
print(f"   3. Documentează diferențele în teză (secțiunea Experimentare)")
