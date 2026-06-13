"""
STEP 3: Detectarea momentelor decisive folosind model MULTICLASS

Input: dataset_training.csv, win_probability_model_3class.pkl
Output: decisive_moments_multiclass.csv, decisive_moments_report_multiclass.txt
"""
import pandas as pd
import numpy as np
import joblib
import warnings
from tqdm import tqdm
warnings.filterwarnings('ignore')

print("=" * 100)
print(" DETECTARE MOMENTE DECISIVE - MODEL MULTICLASS")
print("=" * 100)

# LOAD MODEL 
print("\nincarcare model antrenat...")
model = joblib.load("win_probability_model_3class.pkl")
scaler = joblib.load("scaler_3class.pkl")
feature_cols = joblib.load("feature_cols.pkl")
print(f" Model incarcat (multiclass - 3 rezultate)")

# LOAD DATA
print(f"\nincarcare dataset...")
df = pd.read_csv("../model/dataset_training.csv")
print(
    f" Dataset: {len(df):,} evenimente din {df['match_id'].nunique()} meciuri")

print(f"\nPredictie probabilitati pentru toate evenimentele...")
X = df[feature_cols].copy()
X_scaled = scaler.transform(X)

probabilities = model.predict_proba(X_scaled)

df['p_away'] = probabilities[:, 0]  
df['p_draw'] = probabilities[:, 1]  
df['p_home'] = probabilities[:, 2]  

print(f" Probabilitati calculate")
print(f"   Media P(Away): {df['p_away'].mean():.3f}")
print(f"   Media P(Draw): {df['p_draw'].mean():.3f}")
print(f"   Media P(Home): {df['p_home'].mean():.3f}")

print(f"\nCalcul impact pentru fiecare eveniment...")

df = df.sort_values(['match_id', 'event_id']).reset_index(drop=True)

# Impact = diferenta probabilitatilor inainte vs dupa eveniment
df['p_home_before'] = df.groupby('match_id')['p_home'].shift(1)
df['p_draw_before'] = df.groupby('match_id')['p_draw'].shift(1)
df['p_away_before'] = df.groupby('match_id')['p_away'].shift(1)

# Calculam impact-ul
df['impact_home'] = df['p_home'] - df['p_home_before']
df['impact_draw'] = df['p_draw'] - df['p_draw_before']
df['impact_away'] = df['p_away'] - df['p_away_before']

# Impact absolut = cea mai mare schimbare in orice directie
df['abs_impact'] = df[['impact_home', 'impact_draw', 'impact_away']].abs().max(axis=1)

# Identificam directia dominanta
conditions = [
    df['impact_home'].abs() == df['abs_impact'],
    df['impact_draw'].abs() == df['abs_impact'],
    df['impact_away'].abs() == df['abs_impact']
]
choices = ['home', 'draw', 'away']
df['impact_direction'] = np.select(conditions, choices, default='unknown')

print(f" Impact calculat pentru toate evenimentele")

print(f"\nFiltrare momente decisive...")

# Detectam goluri
df['score_total'] = df['score_home'] + df['score_away']
score_changes = df.groupby('match_id')['score_total'].diff().fillna(0)
df['is_goal'] = (score_changes == 1)

# Detectam cartonase rosii
df['red_total'] = df['red_cards_home'] + df['red_cards_away']
red_changes = df.groupby('match_id')['red_total'].diff().fillna(0)
df['is_red_card'] = (red_changes == 1)

# Detectam penalty-uri
df['is_penalty'] = (df['shot_type'] ==
                    'Penalty') if 'shot_type' in df.columns else False

# Filtram momente decisive: goluri, cartonase rosii sau impact > 3%
decisive_moments = df[
    (df['is_goal']) |
    (df['is_red_card']) |
    (df['is_penalty']) |
    (df['abs_impact'] > 0.03)
].copy()

print(f"✓ Momente decisive: {len(decisive_moments):,}")
print(f"   - Goluri: {decisive_moments['is_goal'].sum()}")
print(f"   - Cartonașe roșii: {decisive_moments['is_red_card'].sum()}")
print(f"   - Penalty-uri: {decisive_moments['is_penalty'].sum()}")
print(
    f"   - Alte (impact >3%): {((decisive_moments['abs_impact'] > 0.03) & ~decisive_moments['is_goal'] & ~decisive_moments['is_red_card']).sum()}")

print(f"\nGenerare descrieri NLP...")

def generate_description_multiclass(row):
    event_type = row['event_type']
    player = row.get('player', 'Unknown')
    minute = int(row['minute'])

    # Determine main event
    if row['is_goal']:
        if row.get('shot_type') == 'Penalty':
            event_desc = f" PENALTY marcat de {player} în minutul {minute}"
        else:
            event_desc = f" GOL marcat de {player} în minutul {minute}"
    elif row['is_red_card']:
        event_desc = f" CARTONAȘ ROȘU pentru {player} în minutul {minute}"
    elif row['is_penalty'] and not row['is_goal']:
        event_desc = f" Penalty RATAT de {player} în minutul {minute}"
    elif event_type == 'Substitution':
        event_desc = f" Schimbare: {player} în minutul {minute}"
    elif event_type == 'Shot':
        event_desc = f" Șut important de {player} în minutul {minute}"
    else:
        event_desc = f" {event_type} de {player} în minutul {minute}"

    # Probability changes
    p_home_before = row.get('p_home_before', 0.5) * 100
    p_draw_before = row.get('p_draw_before', 0.5) * 100
    p_away_before = row.get('p_away_before', 0.5) * 100

    p_home_after = row['p_home'] * 100
    p_draw_after = row['p_draw'] * 100
    p_away_after = row['p_away'] * 100

    prob_desc = (f"Probabilități: Home {p_home_before:.1f}→{p_home_after:.1f}% | "
                 f"Draw {p_draw_before:.1f}→{p_draw_after:.1f}% | "
                 f"Away {p_away_before:.1f}→{p_away_after:.1f}%")

    impact_pct = row['abs_impact'] * 100
    impact_desc = f"Impact maxim: {impact_pct:.1f}% ({row['impact_direction']})"

    return f"{event_desc}\n    {prob_desc}\n    {impact_desc}"


decisive_moments['description'] = decisive_moments.apply(
    generate_description_multiclass, axis=1)

print(f"\n Salvare rezultate...")

decisive_moments_sorted = decisive_moments.sort_values(
    'abs_impact', ascending=False)

top_moments = decisive_moments_sorted.head(200)
output_cols = ['match_id', 'minute', 'event_type', 'player', 'team',
               'p_away_before', 'p_draw_before', 'p_home_before',
               'p_away', 'p_draw', 'p_home',
               'impact_away', 'impact_draw', 'impact_home', 'abs_impact',
               'impact_direction', 'description']

top_moments[output_cols].to_csv("decisive_moments_multiclass.csv", index=False)
print(f" decisive_moments_multiclass.csv salvat (top 200 momente)")

# GENERATE REPORT 
with open("decisive_moments_report_multiclass.txt", "w", encoding="utf-8") as f:
    f.write("=" * 100 + "\n")
    f.write("RAPORT MOMENTE DECISIVE\n")
    f.write("=" * 100 + "\n\n")
    f.write(f"Total momente decisive detectate: {len(decisive_moments):,}\n")
    f.write(f"Top 100 momente cu cel mai mare impact:\n\n")

    for idx, (i, row) in enumerate(top_moments.head(100).iterrows(), 1):
        f.write(f"#{idx}. {row['description']}\n")
        f.write(
            f"    Match ID: {row['match_id']} | Scor: {int(row['score_home'])}-{int(row['score_away'])}\n")
        f.write(f"    xG: {row['xg_home']:.2f} - {row['xg_away']:.2f}\n\n")

print(f"decisive_moments_report_multiclass.txt salvat")

# STATISTICS 
print(f"\nStatistici:")
print(f"   Top impact (home): {decisive_moments['impact_home'].max():.3f}")
print(f"   Top impact (draw): {decisive_moments['impact_draw'].max():.3f}")
print(f"   Top impact (away): {decisive_moments['impact_away'].max():.3f}")
print(f"   Media impact absolut: {decisive_moments['abs_impact'].mean():.3f}")

print(f"\n" + "=" * 100)
print(" DETECTARE COMPLETA!")
print("=" * 100)
