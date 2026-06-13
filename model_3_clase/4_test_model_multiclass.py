"""
Testare model pe un meci specific + vizualizare

"""
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import warnings
import random
warnings.filterwarnings('ignore')

print("=" * 100)
print(" TESTARE MODEL MULTICLASS PE UN MECI")
print("=" * 100)

print("\nincarcare model...")
model = joblib.load("win_probability_model_3class.pkl")
scaler = joblib.load("scaler_3class.pkl")
feature_cols = joblib.load("feature_cols.pkl")
print(f" Model multiclass încărcat")

print(f"\nincarcare dataset...")
df = pd.read_csv("../model/dataset_training.csv")

# Select a random match
available_matches = df['match_id'].unique()
test_match_id = random.choice(available_matches)

print(f"\nMeci selectat random: {test_match_id}")

match_data = df[df['match_id'] == test_match_id].copy()
match_data = match_data.sort_values('timestamp_seconds').reset_index(drop=True)

final_result_raw = match_data['final_result'].iloc[-1]
final_score_home = int(match_data['score_home'].max())
final_score_away = int(match_data['score_away'].max())

result_text = {-1: "VICTORIE OASPETI", 0: "EGAL", 1: "VICTORIE GAZDA"}

print(
    f"   Scor final: {final_score_home}-{final_score_away} ({result_text[final_result_raw]})")
print(f"   Evenimente: {len(match_data)}")

print(f"\nCalcul probabilitati pentru fiecare eveniment...")
X_test = match_data[feature_cols].copy()
X_test_scaled = scaler.transform(X_test)

probabilities = model.predict_proba(X_test_scaled)

match_data['p_away'] = probabilities[:, 0]
match_data['p_draw'] = probabilities[:, 1]
match_data['p_home'] = probabilities[:, 2]

# Calculam impact
match_data['p_home_before'] = match_data['p_home'].shift(1)
match_data['p_draw_before'] = match_data['p_draw'].shift(1)
match_data['p_away_before'] = match_data['p_away'].shift(1)

match_data['impact_home'] = match_data['p_home'] - match_data['p_home_before']
match_data['impact_draw'] = match_data['p_draw'] - match_data['p_draw_before']
match_data['impact_away'] = match_data['p_away'] - match_data['p_away_before']

match_data['abs_impact'] = match_data[['impact_home',
                                       'impact_draw', 'impact_away']].abs().max(axis=1)

print(f"✓ Probabilități calculate")

print(f"\nDetectare momente decisive in meci...")

# Detectam goluri
match_data['score_total'] = match_data['score_home'] + match_data['score_away']
score_changes = match_data['score_total'].diff().fillna(0)
goals = match_data[score_changes == 1]

# Cartonase
match_data['red_total'] = match_data['red_cards_home'] + \
    match_data['red_cards_away']
red_changes = match_data['red_total'].diff().fillna(0)
red_cards = match_data[red_changes == 1]

match_data['yellow_total'] = match_data['yellow_cards_home'] + \
    match_data['yellow_cards_away']
yellow_changes = match_data['yellow_total'].diff().fillna(0)
yellow_cards = match_data[yellow_changes == 1]

# Penalty-uri
if 'shot_type' in match_data.columns:
    penalties = match_data[match_data['shot_type'] == 'Penalty']
else:
    penalties = pd.DataFrame()

# Suturi importante
important_shots = match_data[
    (match_data['event_type'] == 'Shot') &
    (match_data['abs_impact'] > 0.02) &
    ~match_data.index.isin(goals.index) &
    ~match_data.index.isin(penalties.index)
]

# Schimbari
substitutions = match_data[
    (match_data['event_type'] == 'Substitution') &
    (match_data['abs_impact'] > 0.015)
]

# Alte momente decisive
excluded_indices = set(goals.index) | set(red_cards.index) | set(yellow_cards.index) | \
    set(penalties.index) | set(important_shots.index) | set(substitutions.index)
other_decisive = match_data[
    (match_data['abs_impact'] > 0.03) &
    ~match_data.index.isin(excluded_indices)
]

print(f"   Goluri: {len(goals)}")
print(f"   Cartonase rosii: {len(red_cards)}")
print(f"   Cartonase galbene: {len(yellow_cards)}")
print(f"   Penalty-uri: {len(penalties)}")
print(f"   Suturi importante: {len(important_shots)}")
print(f"   Schimbari: {len(substitutions)}")
print(f"   Alte momente: {len(other_decisive)}")

# SAVE
output_file = f"test_match_{test_match_id}_analysis_multiclass.csv"
match_data.to_csv(output_file, index=False)
print(f"\nAnaliza salvata în: {output_file}")

try:
    print("\nGenerez grafic evolutie probabilitati")

    fig, ax = plt.subplots(figsize=(18, 8))

    ax.plot(match_data['minute'], match_data['p_home'] * 100,
            linewidth=2.5, color='#2ca02c', label='P(Victorie GAZDA)', alpha=0.9)
    ax.plot(match_data['minute'], match_data['p_draw'] * 100,
            linewidth=2.5, color='#ff7f0e', label='P(Egal)', alpha=0.9)
    ax.plot(match_data['minute'], match_data['p_away'] * 100,
            linewidth=2.5, color='#d62728', label='P(Victorie OASPETI)', alpha=0.9)

    # Mark events
    if len(goals) > 0:
        ax.scatter(goals['minute'], goals['p_home'] * 100,
                   color='#2ca02c', s=500, marker='*',
                   label=f' Goluri ({len(goals)})', zorder=12,
                   edgecolors='darkgreen', linewidths=2.5)

    if len(penalties) > 0:
        ax.scatter(penalties['minute'], penalties['p_home'] * 100,
                   color='#ff00ff', s=200, marker='D',
                   label=f' Penalty-uri ({len(penalties)})', zorder=11,
                   edgecolors='purple', linewidths=1.5, alpha=0.9)

    if len(red_cards) > 0:
        ax.scatter(red_cards['minute'], red_cards['p_home'] * 100,
                   color='#8B0000', s=180, marker='s',
                   label=f' Cartonase rosii ({len(red_cards)})', zorder=10,
                   edgecolors='black', linewidths=1.5)

    if len(yellow_cards) > 0:
        ax.scatter(yellow_cards['minute'], yellow_cards['p_home'] * 100,
                   color='#FFD700', s=120, marker='v',
                   label=f' Cartonase galbene ({len(yellow_cards)})', zorder=8,
                   edgecolors='orange', linewidths=1, alpha=0.85)

    if len(substitutions) > 0:
        ax.scatter(substitutions['minute'], substitutions['p_home'] * 100,
                   color='#1f77b4', s=140, marker='^',
                   label=f' Schimbari ({len(substitutions)})', zorder=7,
                   edgecolors='darkblue', linewidths=1, alpha=0.8)

    if len(important_shots) > 0:
        ax.scatter(important_shots['minute'], important_shots['p_home'] * 100,
                   color='#bcbd22', s=110, marker='o',
                   label=f' Suturi ({len(important_shots)})', zorder=6,
                   edgecolors='olive', linewidths=1, alpha=0.75)

    if len(other_decisive) > 0:
        ax.scatter(other_decisive['minute'], other_decisive['p_home'] * 100,
                   color='#7f7f7f', s=80, marker='o',
                   label=f' Alte faze ({len(other_decisive)})', zorder=5,
                   edgecolors='black', linewidths=0.8, alpha=0.65)

    ax.axhline(y=33.33, color='gray', linestyle=':', alpha=0.3, linewidth=1)
    ax.axhline(y=66.67, color='gray', linestyle=':', alpha=0.3, linewidth=1)

    ax.set_xlabel('Minute', fontsize=13, fontweight='bold')
    ax.set_ylabel('Probabilitate (%)', fontsize=13, fontweight='bold')
    ax.set_title(f'Evolutia Probabilitatilor - Meci {test_match_id} (MODEL MULTICLASS)\n'
                 f'Scor Final: {final_score_home}-{final_score_away} ({result_text[final_result_raw]})',
                 fontsize=15, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.7)
    ax.legend(fontsize=10, loc='best', framealpha=0.95, ncol=2)
    ax.set_ylim(-5, 105)
    ax.set_xlim(-2, match_data['minute'].max() + 3)

    plot_file = f"test_match_{test_match_id}_plot_multiclass.png"
    plt.tight_layout()
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"Grafic salvat în: {plot_file}")

except Exception as e:
    print(f" Nu s-a putut genera graficul: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 100)
print(" TESTARE COMPLETA!")
print("=" * 100)
print(f"\nFisiere generate:")
print(f"   - {output_file}")
if 'plot_file' in locals():
    print(f"   - {plot_file}")
