"""
Evaluare riguroasa a modelului multiclass

Implementeaza metodele de evaluare din paper-ul academic:
- Ranked Probability Score (RPS)
- Brier Score per clasa
- Calibration Curves
- Accuracy per time frame
- Comparatie cu baseline pre-game

Referinta: Robberechts et al. (2019) "Who Will Win It? 
An In-game Win Probability Model for Football"
"""
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import brier_score_loss, accuracy_score, log_loss
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

print("=" * 100)
print(" EVALUARE RIGUROASA MODEL MULTICLASS")
print("=" * 100)

print("\nincarcare model antrenat...")
model = joblib.load("win_probability_model_3class.pkl")
scaler = joblib.load("scaler_3class.pkl")
feature_cols = joblib.load("feature_cols.pkl")
print(f" Model incarcat")

print(f"\nincarcare dataset...")
df = pd.read_csv("../model/dataset_training.csv")
df['target_multiclass'] = df['final_result'] + 1

# Split pe meciuri
match_ids = df['match_id'].unique()
train_matches, test_matches = train_test_split(
    match_ids, test_size=0.2, random_state=42
)
test_mask = df['match_id'].isin(test_matches)
df_test = df[test_mask].copy()

X_test = df_test[feature_cols]
y_test = df_test['target_multiclass']

X_test_scaled = scaler.transform(X_test)
y_pred_proba = model.predict_proba(X_test_scaled)
y_pred = model.predict(X_test_scaled)

print(
    f" Test set: {len(df_test):,} evenimente din {len(test_matches)} meciuri")

# RANKED PROBABILITY SCORE (RPS)
print(f"\n" + "=" * 100)
print(" RANKED PROBABILITY SCORE (RPS)")
print("=" * 100)

def ranked_probability_score(y_true, y_pred_proba):
    """
    Calculeaza RPS conform paper-ului academic.

    RPS = (1/2) * sum[(cumsum(pred) - cumsum(true))^2]

    y_true: 0=away, 1=draw, 2=home
    y_pred_proba: [P(away), P(draw), P(home)]
    """
    n_samples = len(y_true)
    n_classes = 3

    # Transformam labels in distributie cumulativa
    y_true_cum = np.zeros((n_samples, n_classes))
    for i, label in enumerate(y_true):
        if label == 0: 
            y_true_cum[i] = [1, 1, 1]
        elif label == 1: 
            y_true_cum[i] = [0, 1, 1]
        else: 
            y_true_cum[i] = [0, 0, 1]

    # Probabilitati cumulative
    y_pred_cum = np.cumsum(y_pred_proba, axis=1)

    # RPS 
    rps_per_sample = np.sum((y_pred_cum - y_true_cum)**2, axis=1) / 2

    return np.mean(rps_per_sample), rps_per_sample


rps_mean, rps_per_sample = ranked_probability_score(
    y_test.values, y_pred_proba)

print(f" Ranked Probability Score (RPS): {rps_mean:.4f}")
print(f"   RPS median: {np.median(rps_per_sample):.4f}")
print(f"   RPS std dev: {np.std(rps_per_sample):.4f}")

# BRIER SCORE PER CLASA
print(f"\n" + "=" * 100)
print(" BRIER SCORE PER CLASA")
print("=" * 100)

brier_away = brier_score_loss((y_test == 0).astype(int), y_pred_proba[:, 0])
brier_draw = brier_score_loss((y_test == 1).astype(int), y_pred_proba[:, 1])
brier_home = brier_score_loss((y_test == 2).astype(int), y_pred_proba[:, 2])

print(f" Brier Score (Victorie OASPETI): {brier_away:.4f}")
print(f" Brier Score (Egal):              {brier_draw:.4f}")
print(f" Brier Score (Victorie GAZDA):    {brier_home:.4f}")
print(
    f" Brier Score (Media):             {(brier_away + brier_draw + brier_home)/3:.4f}")

# CALIBRATION CURVES
print(f"\n" + "=" * 100)
print(" CALIBRATION CURVES")
print("=" * 100)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
outcomes = ['Victorie OASPETI', 'Egal', 'Victorie GAZDA']
colors = ['#d62728', '#ff7f0e', '#2ca02c']

for idx, (outcome_name, color) in enumerate(zip(outcomes, colors)):
    ax = axes[idx]

    # Calculam calibration curve
    prob_true, prob_pred = calibration_curve(
        (y_test == idx).astype(int),
        y_pred_proba[:, idx],
        n_bins=10,
        strategy='uniform'
    )

    # Plot
    ax.plot([0, 1], [0, 1], 'k--', linewidth=2, label='Perfect calibration')
    ax.plot(prob_pred, prob_true, marker='o', linewidth=2,
            markersize=8, color=color, label='Your model')

    # Umplem intre perfect si actual
    ax.fill_between(prob_pred, prob_true, prob_pred, alpha=0.2, color=color)

    ax.set_xlabel('Predicted Probability', fontsize=12, fontweight='bold')
    ax.set_ylabel('Actual Frequency', fontsize=12, fontweight='bold')
    ax.set_title(f'Calibration: {outcome_name}',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('calibration_curves_multiclass.png', dpi=150, bbox_inches='tight')
print(f" Grafic salvat: calibration_curves_multiclass.png")

# Calculam calibration error
cal_errors = []
for idx in range(3):
    prob_true, prob_pred = calibration_curve(
        (y_test == idx).astype(int),
        y_pred_proba[:, idx],
        n_bins=10,
        strategy='uniform'
    )
    cal_error = np.mean(np.abs(prob_true - prob_pred))
    cal_errors.append(cal_error)
    print(f"   Calibration Error ({outcomes[idx]}): {cal_error:.4f}")

print(f"   Mean Calibration Error: {np.mean(cal_errors):.4f}")

# ACCURACY PER TIME FRAME
print(f"\n" + "=" * 100)
print(" ACCURACY PER TIME FRAME")
print("=" * 100)

df_test['time_frame'] = ((df_test['minute'] / 94) *
                         100).astype(int).clip(0, 99)

time_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
accuracies = []
rps_scores = []
sample_sizes = []

for i in range(len(time_bins) - 1):
    t_start, t_end = time_bins[i], time_bins[i+1]
    mask = (df_test['time_frame'] >= t_start) & (df_test['time_frame'] < t_end)

    if mask.sum() > 0:
        acc = accuracy_score(y_test[mask], y_pred[mask])
        rps_bin, _ = ranked_probability_score(
            y_test[mask].values,
            y_pred_proba[mask]
        )
        accuracies.append(acc)
        rps_scores.append(rps_bin)
        sample_sizes.append(mask.sum())
    else:
        accuracies.append(np.nan)
        rps_scores.append(np.nan)
        sample_sizes.append(0)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Graficul de accuracy
time_labels = [
    f"{time_bins[i]}-{time_bins[i+1]}%" for i in range(len(time_bins)-1)]
ax1.plot(range(len(accuracies)), accuracies, marker='o', linewidth=2.5,
         markersize=8, color='#1f77b4', label='Accuracy')
ax1.axhline(y=accuracy_score(y_test, y_pred), color='gray', linestyle='--',
            linewidth=2, label='Overall Accuracy')
ax1.set_xlabel('Game Progress', fontsize=12, fontweight='bold')
ax1.set_ylabel('Accuracy', fontsize=12, fontweight='bold')
ax1.set_title('Accuracy per Time Frame', fontsize=14, fontweight='bold')
ax1.set_xticks(range(len(time_labels)))
ax1.set_xticklabels(time_labels, rotation=45)
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=11)
ax1.set_ylim(0.3, 1.0)

# Graficul de RPS
ax2.plot(range(len(rps_scores)), rps_scores, marker='s', linewidth=2.5,
         markersize=8, color='#ff7f0e', label='RPS')
ax2.axhline(y=rps_mean, color='gray', linestyle='--',
            linewidth=2, label='Overall RPS')
ax2.set_xlabel('Game Progress', fontsize=12, fontweight='bold')
ax2.set_ylabel('RPS (lower is better)', fontsize=12, fontweight='bold')
ax2.set_title('RPS per Time Frame', fontsize=14, fontweight='bold')
ax2.set_xticks(range(len(time_labels)))
ax2.set_xticklabels(time_labels, rotation=45)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=11)

plt.tight_layout()
plt.savefig('accuracy_per_timeframe.png', dpi=150, bbox_inches='tight')
print(f" Grafic salvat: accuracy_per_timeframe.png\n")

for i, (acc, rps, size) in enumerate(zip(accuracies, rps_scores, sample_sizes)):
    if not np.isnan(acc):
        print(
            f"   {time_labels[i]:10s}: Acc={acc:.3f}, RPS={rps:.4f} ({size:,} samples)")

# COMPARAȚIE CU BASELINE
print(f"\n" + "=" * 100)
print(" COMPARAȚIE CU BASELINE")
print("=" * 100)

print(" Baseline 1: Score-Only Model")

X_train_baseline = df[~test_mask][['score_diff']].copy()
y_train_baseline = df[~test_mask]['target_multiclass']
X_test_baseline = df_test[['score_diff']].copy()

scaler_baseline = StandardScaler()
X_train_baseline_scaled = scaler_baseline.fit_transform(X_train_baseline)
X_test_baseline_scaled = scaler_baseline.transform(X_test_baseline)

baseline_model = LogisticRegression(random_state=42, max_iter=1000)
baseline_model.fit(X_train_baseline_scaled, y_train_baseline)

y_pred_baseline_proba = baseline_model.predict_proba(X_test_baseline_scaled)
y_pred_baseline = baseline_model.predict(X_test_baseline_scaled)

baseline_acc = accuracy_score(y_test, y_pred_baseline)
baseline_rps, _ = ranked_probability_score(
    y_test.values, y_pred_baseline_proba)

print(f"   Accuracy: {baseline_acc:.4f}")
print(f"   RPS:      {baseline_rps:.4f}")

print(f"\n Baseline 2: Naive Uniform")
print("   (33.3% pentru fiecare outcome - worst case)\n")

y_pred_uniform_proba = np.ones((len(y_test), 3)) / 3  # 33.3% each
uniform_rps, _ = ranked_probability_score(y_test.values, y_pred_uniform_proba)

print(f"   RPS:      {uniform_rps:.4f}")

# Your model
print(f"\n Your Full Model (All in-game features):")
print(f"   Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(f"   RPS:      {rps_mean:.4f}")

# Improvements
improvement_acc = accuracy_score(y_test, y_pred) - baseline_acc
improvement_rps_score = baseline_rps - rps_mean
improvement_rps_uniform = uniform_rps - rps_mean

print(f"\n Improvement over Score-Only:")
print(
    f"   Accuracy: +{improvement_acc:.4f} ({improvement_acc/baseline_acc*100:+.1f}%)")
print(
    f"   RPS:      {improvement_rps_score:+.4f} ({improvement_rps_score/baseline_rps*100:+.1f}% better)")

print(f"\n✨ Improvement over Uniform:")
print(
    f"   RPS:      {improvement_rps_uniform:+.4f} ({improvement_rps_uniform/uniform_rps*100:+.1f}% better)")

baseline_score_acc = baseline_acc
baseline_score_rps = baseline_rps
baseline_uniform_rps = uniform_rps

print(f"\n" + "=" * 100)
print(" ANALIZA DISTRIBUTIEI PROBABILITATILOR")
print("=" * 100)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

for idx, (outcome_name, color) in enumerate(zip(outcomes, colors)):
    ax = axes[idx]

    # Graficul de histograma
    ax.hist(y_pred_proba[:, idx], bins=30, alpha=0.7,
            color=color, edgecolor='black')
    ax.axvline(y_pred_proba[:, idx].mean(), color='red', linestyle='--',
               linewidth=2, label=f'Mean: {y_pred_proba[:, idx].mean():.3f}')
    ax.set_xlabel('Predicted Probability', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title(f'Distribution: {outcome_name}',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('probability_distributions.png', dpi=150, bbox_inches='tight')
print(f" Grafic salvat: probability_distributions.png\n")

for idx, outcome_name in enumerate(outcomes):
    mean_prob = y_pred_proba[:, idx].mean()
    std_prob = y_pred_proba[:, idx].std()
    print(f"   {outcome_name:20s}: mean={mean_prob:.3f}, std={std_prob:.3f}")

# SAVE RESULTS
results = {
    'RPS': rps_mean,
    'RPS_median': np.median(rps_per_sample),
    'RPS_std': np.std(rps_per_sample),
    'Brier_Away': brier_away,
    'Brier_Draw': brier_draw,
    'Brier_Home': brier_home,
    'Brier_Mean': (brier_away + brier_draw + brier_home) / 3,
    'Accuracy': accuracy_score(y_test, y_pred),
    'Log_Loss': log_loss(y_test, y_pred_proba),
    'Mean_Calibration_Error': np.mean(cal_errors),
    'Baseline_ScoreOnly_Acc': baseline_score_acc,
    'Baseline_ScoreOnly_RPS': baseline_score_rps,
    'Baseline_Uniform_RPS': baseline_uniform_rps,
    'Improvement_vs_ScoreOnly_Acc': accuracy_score(y_test, y_pred) - baseline_score_acc,
    'Improvement_vs_ScoreOnly_RPS': baseline_score_rps - rps_mean,
    'Improvement_vs_Uniform_RPS': baseline_uniform_rps - rps_mean,
}

results_df = pd.DataFrame([results])
results_df.to_csv('evaluation_results.csv', index=False)
print(f"\n Rezultate salvate in: evaluation_results.csv")

# SUMMARY
print(f"\n" + "=" * 100)
print(" EVALUARE COMPLETA!")
print("=" * 100)
print(f"\n Fisiere generate:")
print(f"   - calibration_curves_multiclass.png")
print(f"   - accuracy_per_timeframe.png")
print(f"   - probability_distributions.png")
print(f"   - evaluation_results.csv")

print(f"\n REZUMAT METRICI:")
print(f"   RPS:              {rps_mean:.4f} (mai mic = mai bun)")
print(
    f"   Brier Score:      {(brier_away + brier_draw + brier_home)/3:.4f} (mai mic = mai bun)")
print(f"   Accuracy:         {accuracy_score(y_test, y_pred):.4f}")
print(f"   Calibration Err:  {np.mean(cal_errors):.4f} (mai mic = mai bun)")

print(f"\n COMPARAȚIE CU BASELINES:")
print(
    f"   Score-Only:  RPS={baseline_score_rps:.4f}, Acc={baseline_score_acc:.4f}")
print(f"   Uniform:     RPS={baseline_uniform_rps:.4f}")
print(
    f"   Your Model:  RPS={rps_mean:.4f}, Acc={accuracy_score(y_test, y_pred):.4f}")
print(
    f"   Improvement: {(baseline_score_rps - rps_mean)/baseline_score_rps*100:.1f}% better than Score-Only!")