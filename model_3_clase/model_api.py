"""
WIN PROBABILITY MODEL - API-Ready Service
===========================================

Microservice pentru predicție win probability în fotbal.
Pregătit pentru integrare Docker cu frontend React + backend C#.

Endpoints simulate:
- /predict - Predicție pentru un singur event
- /predict-batch - Predicții pentru un meci complet
- /evaluate - Metrici complete model
- /health - Health check

Output: JSON + diagrame salvate în ./api_output/
"""

from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Docker

# === CONFIGURARE ===
OUTPUT_DIR = Path("./api_output")
OUTPUT_DIR.mkdir(exist_ok=True)

CHART_OUTPUT_DIR = OUTPUT_DIR / "charts"
JSON_OUTPUT_DIR = OUTPUT_DIR / "json"

CHART_OUTPUT_DIR.mkdir(exist_ok=True)
JSON_OUTPUT_DIR.mkdir(exist_ok=True)

MODEL_PATH = "win_probability_model_3class.pkl"
SCALER_PATH = "scaler_3class.pkl"
FEATURES_PATH = "feature_cols.pkl"
DATASET_PATH = "../model/dataset_training.csv"

# Target mapping
TARGET_LABELS = {
    0: "away_win",
    1: "draw",
    2: "home_win"
}

TARGET_LABELS_RO = {
    0: "Victorie Oaspeți",
    1: "Egal",
    2: "Victorie Gazdă"
}


class WinProbabilityModel:
    """Model wrapper pentru predicții win probability"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.loaded = False

    def load_model(self) -> Dict:
        """Încarcă modelul și dependințele"""
        try:
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            self.feature_cols = joblib.load(FEATURES_PATH)
            self.loaded = True

            return {
                "status": "success",
                "message": "Model loaded successfully",
                "features_count": len(self.feature_cols),
                "model_type": str(type(self.model).__name__)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to load model: {str(e)}"
            }

    def predict_single(self, features: Dict) -> Dict:
        """
        Predicție pentru un singur event

        Args:
            features: Dictionary cu features (ex: {'minute': 45, 'score_diff': 1, ...})

        Returns:
            Dictionary cu probabilități și metadata
        """
        if not self.loaded:
            return {"status": "error", "message": "Model not loaded"}

        try:
            # Validare features
            missing = set(self.feature_cols) - set(features.keys())
            if missing:
                return {
                    "status": "error",
                    "message": f"Missing features: {list(missing)}"
                }

            # Pregătire input
            X = pd.DataFrame([features])[self.feature_cols]
            X_scaled = self.scaler.transform(X)

            # Predicție
            probabilities = self.model.predict_proba(X_scaled)[0]
            prediction = self.model.predict(X_scaled)[0]

            return {
                "status": "success",
                "prediction": {
                    "predicted_outcome": TARGET_LABELS[prediction],
                    "predicted_outcome_ro": TARGET_LABELS_RO[prediction],
                    "probabilities": {
                        "away_win": float(probabilities[0]),
                        "draw": float(probabilities[1]),
                        "home_win": float(probabilities[2])
                    },
                    "confidence": float(probabilities[prediction])
                },
                "input": {
                    "minute": features.get('minute', 0),
                    "score_diff": features.get('score_diff', 0),
                    "xg_diff": features.get('xg_diff', 0.0)
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Prediction failed: {str(e)}"
            }

    def predict_match(self, match_id: int, dataset_path: str = DATASET_PATH) -> Dict:
        """
        Predicții pentru toate evenimentele unui meci

        Args:
            match_id: ID-ul meciului
            dataset_path: Path la dataset

        Returns:
            Dictionary cu predicții temporale și metrici
        """
        if not self.loaded:
            return {"status": "error", "message": "Model not loaded"}

        try:
            # Încărcare date meci
            df = pd.read_csv(dataset_path)

            # Creare target multiclass (consistency cu training)
            df['target_multiclass'] = df['final_result'] + 1

            match_data = df[df['match_id'] == match_id].copy()

            if len(match_data) == 0:
                return {
                    "status": "error",
                    "message": f"Match {match_id} not found"
                }

            # Pregătire features
            X = match_data[self.feature_cols]
            X_scaled = self.scaler.transform(X)

            # Predicții
            probabilities = self.model.predict_proba(X_scaled)
            predictions = self.model.predict(X_scaled)

            # Rezultat final real
            final_result = int(match_data['target_multiclass'].iloc[-1])
            final_score_home = int(match_data['score_home'].max())
            final_score_away = int(match_data['score_away'].max())

            # Timeline predicții (sample la fiecare 5 minute)
            timeline = []
            for idx in range(0, len(match_data), max(1, len(match_data) // 20)):
                row = match_data.iloc[idx]
                prob = probabilities[idx]

                timeline.append({
                    "minute": int(row['minute']),
                    "timestamp_seconds": int(row['timestamp_seconds']),
                    "score": f"{int(row['score_home'])}-{int(row['score_away'])}",
                    "probabilities": {
                        "away_win": float(prob[0]),
                        "draw": float(prob[1]),
                        "home_win": float(prob[2])
                    },
                    "predicted_outcome": TARGET_LABELS[predictions[idx]]
                })

            # Predicție finală
            final_prob = probabilities[-1]
            final_pred = predictions[-1]

            # Extragere evenimente cheie și insights
            key_events, match_insights = self._extract_key_events(
                match_data, probabilities, predictions
            )

            # Generare grafic
            chart_path = self._generate_match_chart(
                match_id,
                match_data,
                probabilities,
                final_score_home,
                final_score_away,
                final_result
            )

            # Construire rezultat JSON
            result = {
                "status": "success",
                "match_info": {
                    "match_id": match_id,
                    "final_score": f"{final_score_home}-{final_score_away}",
                    "actual_result": TARGET_LABELS[final_result],
                    "actual_result_ro": TARGET_LABELS_RO[final_result],
                    "total_events": len(match_data)
                },
                "final_prediction": {
                    "predicted_outcome": TARGET_LABELS[final_pred],
                    "predicted_outcome_ro": TARGET_LABELS_RO[final_pred],
                    "probabilities": {
                        "away_win": float(final_prob[0]),
                        "draw": float(final_prob[1]),
                        "home_win": float(final_prob[2])
                    },
                    "confidence": float(np.max(final_prob)),
                    "correct": bool(final_pred == final_result)
                },
                "key_events": key_events,
                "match_insights": match_insights,
                "timeline": timeline,
                "chart": str(chart_path),
                "timestamp": datetime.now().isoformat()
            }

            # Salvare JSON în api_output/json/
            json_output_path = JSON_OUTPUT_DIR / \
                f"match_{match_id}_prediction.json"
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"\n✅ JSON saved to: {json_output_path}")

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Match prediction failed: {str(e)}"
            }

    def _extract_key_events(
        self,
        match_data: pd.DataFrame,
        probabilities: np.ndarray,
        predictions: np.ndarray
    ) -> tuple[list, dict]:
        """
        Extrage evenimente cheie și insights din meci

        Args:
            match_data: DataFrame cu date meci
            probabilities: Array cu probabilități
            predictions: Array cu predicții

        Returns:
            tuple[list, dict]: (key_events, match_insights)
        """
        key_events = []

        # Track score changes (goals)
        prev_score_home = 0
        prev_score_away = 0
        prev_prob = None

        # Track probability swings
        swing_threshold = 0.10  # 10% change = significant

        for idx, row in match_data.iterrows():
            minute = int(row['minute'])
            score_home = int(row['score_home'])
            score_away = int(row['score_away'])
            prob = probabilities[idx - match_data.index[0]]

            event_details = {
                "minute": minute,
                "score": f"{score_home}-{score_away}",
                "probabilities": {
                    "away_win": float(prob[0]),
                    "draw": float(prob[1]),
                    "home_win": float(prob[2])
                }
            }

            # Detect GOALS
            if score_home > prev_score_home:
                prob_change = float(
                    prob[2] - prev_prob[2]) if prev_prob is not None else 0
                key_events.append({
                    **event_details,
                    "type": "goal_home",
                    "description": f"Home team goal - prob shifted {prob_change:+.1%}",
                    "impact": "critical" if abs(prob_change) > 0.15 else "high",
                    "probability_change": float(prob_change) if prev_prob is not None else None
                })

            if score_away > prev_score_away:
                prob_change = float(
                    prob[0] - prev_prob[0]) if prev_prob is not None else 0
                key_events.append({
                    **event_details,
                    "type": "goal_away",
                    "description": f"Away team goal - prob shifted {prob_change:+.1%}",
                    "impact": "critical" if abs(prob_change) > 0.15 else "high",
                    "probability_change": float(prob_change) if prev_prob is not None else None
                })

            # Detect RED CARDS
            if idx > match_data.index[0]:
                prev_row = match_data.iloc[idx - match_data.index[0] - 1]
                if row['red_cards_home'] > prev_row['red_cards_home']:
                    key_events.append({
                        **event_details,
                        "type": "red_card_home",
                        "description": f"Home team red card at {minute}'",
                        "impact": "critical"
                    })
                if row['red_cards_away'] > prev_row['red_cards_away']:
                    key_events.append({
                        **event_details,
                        "type": "red_card_away",
                        "description": f"Away team red card at {minute}'",
                        "impact": "critical"
                    })

            # Detect TURNING POINTS (significant probability swings)
            if prev_prob is not None and score_home == prev_score_home and score_away == prev_score_away:
                # Only detect swings when score didn't change (otherwise it's captured as goal)
                max_swing = max(
                    abs(prob[0] - prev_prob[0]),
                    abs(prob[1] - prev_prob[1]),
                    abs(prob[2] - prev_prob[2])
                )

                if max_swing > swing_threshold:
                    # Determine which outcome swung
                    swing_type = "unknown"
                    if abs(prob[2] - prev_prob[2]) == max_swing:
                        swing_type = "home_momentum" if prob[2] > prev_prob[2] else "away_momentum"
                    elif abs(prob[0] - prev_prob[0]) == max_swing:
                        swing_type = "away_momentum" if prob[0] > prev_prob[0] else "home_momentum"

                    key_events.append({
                        **event_details,
                        "type": "turning_point",
                        "swing_type": swing_type,
                        "description": f"Significant momentum shift ({max_swing:.1%})",
                        "impact": "high" if max_swing > 0.15 else "medium",
                        "probability_change": float(max_swing)
                    })

            prev_score_home = score_home
            prev_score_away = score_away
            prev_prob = prob

        # Calculate MATCH INSIGHTS
        insights = self._calculate_match_insights(
            match_data, probabilities, predictions, key_events
        )

        return key_events, insights

    def _calculate_match_insights(
        self,
        match_data: pd.DataFrame,
        probabilities: np.ndarray,
        predictions: np.ndarray,
        key_events: list
    ) -> dict:
        """
        Calculează insights agregați despre meci
        """
        # Biggest probability swing
        biggest_swing = {
            "minute": 0,
            "change": 0.0,
            "description": "No significant swings"
        }

        for event in key_events:
            if event.get("probability_change") and abs(event["probability_change"]) > biggest_swing["change"]:
                biggest_swing = {
                    "minute": event["minute"],
                    "change": float(abs(event["probability_change"])),
                    "description": event["description"],
                    "type": event["type"]
                }

        # Count turning points by type
        goals_home = len([e for e in key_events if e["type"] == "goal_home"])
        goals_away = len([e for e in key_events if e["type"] == "goal_away"])
        turning_points = len(
            [e for e in key_events if e["type"] == "turning_point"])
        red_cards = len([e for e in key_events if "red_card" in e["type"]])

        # Analyze dominance periods (every 15 minutes)
        dominance_periods = []
        time_bins = [(0, 15), (15, 30), (30, 45), (45, 60), (60, 75), (75, 96)]

        for start, end in time_bins:
            period_data = match_data[
                (match_data['minute'] >= start) & (match_data['minute'] < end)
            ]
            if len(period_data) > 0:
                indices = period_data.index - match_data.index[0]
                period_probs = probabilities[indices]

                avg_home = float(np.mean(period_probs[:, 2]))
                avg_draw = float(np.mean(period_probs[:, 1]))
                avg_away = float(np.mean(period_probs[:, 0]))

                dominant_team = "home" if avg_home > max(avg_draw, avg_away) else (
                    "away" if avg_away > avg_draw else "balanced"
                )

                dominance_periods.append({
                    "period": f"{start}-{end}'",
                    "dominant_team": dominant_team,
                    "avg_probabilities": {
                        "home_win": avg_home,
                        "draw": avg_draw,
                        "away_win": avg_away
                    }
                })

        # Find most volatile period (highest std deviation)
        volatility_by_period = []
        for period in dominance_periods:
            start, end = map(int, period["period"].replace("'", "").split("-"))
            period_data = match_data[
                (match_data['minute'] >= start) & (match_data['minute'] < end)
            ]
            if len(period_data) > 5:
                indices = period_data.index - match_data.index[0]
                period_probs = probabilities[indices]
                # std of home win prob
                volatility = float(np.std(period_probs[:, 2]))
                volatility_by_period.append((period["period"], volatility))

        most_volatile_period = max(volatility_by_period, key=lambda x: x[1])[
            0] if volatility_by_period else "N/A"

        # Final statistics
        final_xg_home = float(match_data['xg_home'].iloc[-1])
        final_xg_away = float(match_data['xg_away'].iloc[-1])
        final_shots_home = int(match_data['shots_home'].iloc[-1])
        final_shots_away = int(match_data['shots_away'].iloc[-1])
        final_passes_home = int(match_data['passes_home'].iloc[-1])
        final_passes_away = int(match_data['passes_away'].iloc[-1])

        return {
            "total_goals": goals_home + goals_away,
            "goals_breakdown": {
                "home": goals_home,
                "away": goals_away
            },
            "total_turning_points": turning_points,
            "total_red_cards": red_cards,
            "biggest_swing": biggest_swing,
            "most_volatile_period": most_volatile_period,
            "dominance_periods": dominance_periods,
            "final_statistics": {
                "xg": {"home": final_xg_home, "away": final_xg_away},
                "shots": {"home": final_shots_home, "away": final_shots_away},
                "passes": {"home": final_passes_home, "away": final_passes_away}
            }
        }

    def _generate_match_chart(
        self,
        match_id: int,
        match_data: pd.DataFrame,
        probabilities: np.ndarray,
        final_score_home: int,
        final_score_away: int,
        final_result: int
    ) -> Path:
        """Generează grafic win probability pentru un meci"""

        fig, ax = plt.subplots(figsize=(14, 7))

        minutes = match_data['timestamp_seconds'] / 60

        # Plot probabilități
        ax.plot(minutes, probabilities[:, 2], 'b-',
                linewidth=2, label='Home Win', alpha=0.8)
        ax.plot(minutes, probabilities[:, 1], 'gray',
                linewidth=2, label='Draw', alpha=0.6)
        ax.plot(minutes, probabilities[:, 0], 'r-',
                linewidth=2, label='Away Win', alpha=0.8)

        # Fundal pentru outcome real
        if final_result == 2:
            ax.axhspan(0, 1, alpha=0.05, color='blue')
        elif final_result == 0:
            ax.axhspan(0, 1, alpha=0.05, color='red')
        else:
            ax.axhspan(0, 1, alpha=0.05, color='gray')

        # Marker goluri
        goals = match_data[match_data[['score_home',
                                       'score_away']].diff().sum(axis=1) != 0]
        for _, goal in goals.iterrows():
            minute = goal['timestamp_seconds'] / 60
            ax.axvline(minute, color='green', linestyle='--',
                       alpha=0.3, linewidth=1)

        ax.set_xlabel('Minute', fontsize=12)
        ax.set_ylabel('Win Probability', fontsize=12)
        ax.set_title(
            f'Match {match_id} - Win Probability Evolution\n'
            f'Final Score: {final_score_home}-{final_score_away} ({TARGET_LABELS_RO[final_result]})',
            fontsize=14, pad=20
        )
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(minutes))
        ax.set_ylim(0, 1)

        # Salvare
        chart_path = CHART_OUTPUT_DIR / f"match_{match_id}_probability.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()

        return chart_path


def evaluate_model_full(save_json: bool = True) -> Dict:
    """
    Evaluare completă model cu toate metricile

    Returns:
        Dictionary cu metrici + paths la grafice
    """
    print("=" * 80)
    print("📊 EVALUARE MODEL - API Output")
    print("=" * 80)

    # Încărcare model
    model_wrapper = WinProbabilityModel()
    load_result = model_wrapper.load_model()

    if load_result["status"] != "success":
        return load_result

    print("✓ Model loaded")

    # Încărcare date
    df = pd.read_csv(DATASET_PATH)

    # Creare target multiclass (exact ca în 2_train_model_multiclass.py)
    # Convertim final_result (-1, 0, 1) în (0, 1, 2) pentru sklearn
    # -1 (away wins) → 0
    #  0 (draw)      → 1
    #  1 (home wins) → 2
    df['target_multiclass'] = df['final_result'] + 1

    # Split train/test (same as training)
    matches = df['match_id'].unique()
    np.random.seed(42)
    test_size = int(len(matches) * 0.2)
    test_matches = np.random.choice(matches, size=test_size, replace=False)

    test_df = df[df['match_id'].isin(test_matches)]

    X_test = test_df[model_wrapper.feature_cols]
    y_test = test_df['target_multiclass']
    X_test_scaled = model_wrapper.scaler.transform(X_test)

    print(f"✓ Test set: {len(test_df):,} events, {len(test_matches)} matches")

    # Predicții
    y_pred = model_wrapper.model.predict(X_test_scaled)
    y_pred_proba = model_wrapper.model.predict_proba(X_test_scaled)

    # === METRICI ===

    # 1. RPS (Ranked Probability Score)
    rps_scores = []
    for true_class, pred_probs in zip(y_test, y_pred_proba):
        cumulative_pred = np.cumsum(pred_probs)
        cumulative_true = np.cumsum(
            [1 if i == true_class else 0 for i in range(3)])
        rps = np.sum((cumulative_pred - cumulative_true) ** 2) / 2
        rps_scores.append(rps)

    rps_mean = float(np.mean(rps_scores))
    rps_median = float(np.median(rps_scores))
    rps_std = float(np.std(rps_scores))

    # 2. Brier Score per clasă
    brier_scores = {}
    for class_idx in range(3):
        true_binary = (y_test == class_idx).astype(int)
        pred_prob = y_pred_proba[:, class_idx]
        brier = float(np.mean((pred_prob - true_binary) ** 2))
        brier_scores[TARGET_LABELS[class_idx]] = brier

    brier_mean = float(np.mean(list(brier_scores.values())))

    # 3. Accuracy
    accuracy = float(accuracy_score(y_test, y_pred))

    # 4. Calibration Error
    calibration_errors = {}
    for class_idx in range(3):
        n_bins = 10
        true_binary = (y_test == class_idx).astype(int).values
        pred_prob = y_pred_proba[:, class_idx]

        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_errors = []

        for i in range(n_bins):
            mask = (pred_prob >= bin_edges[i]) & (pred_prob < bin_edges[i + 1])
            if mask.sum() > 0:
                avg_pred = pred_prob[mask].mean()
                avg_true = true_binary[mask].mean()
                bin_errors.append(abs(avg_pred - avg_true))

        calibration_errors[TARGET_LABELS[class_idx]] = float(
            np.mean(bin_errors)) if bin_errors else 0.0

    calibration_mean = float(np.mean(list(calibration_errors.values())))

    # 5. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)

    # 6. Accuracy per timeframe
    test_df_pred = test_df.copy()
    test_df_pred['predicted'] = y_pred
    test_df_pred['correct'] = (y_pred == y_test.values)

    timeframe_stats = []
    for i in range(10):
        start_pct = i * 10
        end_pct = (i + 1) * 10

        max_time = test_df_pred.groupby('match_id')['timestamp_seconds'].max()
        mask = test_df_pred.apply(
            lambda row: (row['timestamp_seconds'] / max_time[row['match_id']] * 100) >= start_pct and
            (row['timestamp_seconds'] / max_time[row['match_id']] * 100) < end_pct,
            axis=1
        )

        if mask.sum() > 0:
            data_slice = test_df_pred[mask]
            acc = data_slice['correct'].mean()

            # RPS for timeframe
            rps_timeframe = []
            for idx in data_slice.index:
                true_class = y_test.loc[idx]
                pred_probs = y_pred_proba[test_df.index.get_loc(idx)]
                cumulative_pred = np.cumsum(pred_probs)
                cumulative_true = np.cumsum(
                    [1 if j == true_class else 0 for j in range(3)])
                rps = np.sum((cumulative_pred - cumulative_true) ** 2) / 2
                rps_timeframe.append(rps)

            timeframe_stats.append({
                "timeframe": f"{start_pct}-{end_pct}%",
                "accuracy": float(acc),
                "rps": float(np.mean(rps_timeframe)),
                "samples": int(mask.sum())
            })

    # === GRAFICE ===

    # 1. Confusion Matrix
    cm_path = CHART_OUTPUT_DIR / "confusion_matrix.png"
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=list(TARGET_LABELS_RO.values()),
                yticklabels=list(TARGET_LABELS_RO.values()))
    plt.title('Confusion Matrix', fontsize=14, pad=15)
    plt.ylabel('Actual', fontsize=12)
    plt.xlabel('Predicted', fontsize=12)
    plt.tight_layout()
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    plt.close()

    # 2. Accuracy per Timeframe
    acc_path = CHART_OUTPUT_DIR / "accuracy_timeframe.png"
    plt.figure(figsize=(12, 6))
    timeframes = [x['timeframe'] for x in timeframe_stats]
    accuracies = [x['accuracy'] for x in timeframe_stats]
    plt.plot(range(len(timeframes)), accuracies,
             'o-', linewidth=2, markersize=8)
    plt.xlabel('Match Progress', fontsize=12)
    plt.ylabel('Accuracy', fontsize=12)
    plt.title('Model Accuracy by Timeframe', fontsize=14, pad=15)
    plt.xticks(range(len(timeframes)), timeframes, rotation=45)
    plt.ylim(0.4, 1.0)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(acc_path, dpi=150, bbox_inches='tight')
    plt.close()

    # 3. Calibration Curves
    cal_path = CHART_OUTPUT_DIR / "calibration_curves.png"
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for class_idx, ax in enumerate(axes):
        n_bins = 10
        true_binary = (y_test == class_idx).astype(int).values
        pred_prob = y_pred_proba[:, class_idx]

        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_pred = []
        bin_true = []

        for i in range(n_bins):
            mask = (pred_prob >= bin_edges[i]) & (pred_prob < bin_edges[i + 1])
            if mask.sum() > 0:
                bin_pred.append(pred_prob[mask].mean())
                bin_true.append(true_binary[mask].mean())

        ax.plot([0, 1], [0, 1], 'k--', linewidth=1,
                label='Perfect Calibration')
        ax.plot(bin_pred, bin_true, 'o-', linewidth=2,
                markersize=8, label='Model')
        ax.set_xlabel('Predicted Probability', fontsize=10)
        ax.set_ylabel('Observed Frequency', fontsize=10)
        ax.set_title(TARGET_LABELS_RO[class_idx], fontsize=12)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(cal_path, dpi=150, bbox_inches='tight')
    plt.close()

    # === JSON OUTPUT ===

    result = {
        "status": "success",
        "evaluation_timestamp": datetime.now().isoformat(),
        "model_info": {
            "model_type": load_result["model_type"],
            "features_count": load_result["features_count"],
            "test_samples": len(test_df),
            "test_matches": len(test_matches)
        },
        "metrics": {
            "rps": {
                "mean": rps_mean,
                "median": rps_median,
                "std": rps_std
            },
            "brier_score": {
                "away_win": brier_scores["away_win"],
                "draw": brier_scores["draw"],
                "home_win": brier_scores["home_win"],
                "mean": brier_mean
            },
            "calibration_error": {
                "away_win": calibration_errors["away_win"],
                "draw": calibration_errors["draw"],
                "home_win": calibration_errors["home_win"],
                "mean": calibration_mean
            },
            "accuracy": accuracy
        },
        "confusion_matrix": cm.tolist(),
        "timeframe_analysis": timeframe_stats,
        "charts": {
            "confusion_matrix": str(cm_path),
            "accuracy_timeframe": str(acc_path),
            "calibration_curves": str(cal_path)
        },
        "summary": {
            "rating": "excellent" if rps_mean < 0.20 and calibration_mean < 0.05 else "good" if rps_mean < 0.25 else "acceptable",
            "interpretation": {
                "rps": f"{'Excellent' if rps_mean < 0.20 else 'Good'} - Model predictions are highly accurate",
                "calibration": f"{'Excellent' if calibration_mean < 0.05 else 'Good'} - Probabilities are trustworthy",
                "accuracy": f"{accuracy*100:.1f}% - Strong predictive performance"
            }
        }
    }

    # Salvare JSON
    if save_json:
        json_path = JSON_OUTPUT_DIR / "evaluation_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        result["output_file"] = str(json_path)
        print(f"✓ JSON saved: {json_path}")

    print(f"✓ Charts saved in: {OUTPUT_DIR / 'charts'}")
    print("=" * 80)

    return result


def health_check() -> Dict:
    """Health check endpoint pentru Docker/Kubernetes"""
    try:
        model_exists = os.path.exists(MODEL_PATH)
        scaler_exists = os.path.exists(SCALER_PATH)
        features_exists = os.path.exists(FEATURES_PATH)

        return {
            "status": "healthy" if all([model_exists, scaler_exists, features_exists]) else "degraded",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "model_file": model_exists,
                "scaler_file": scaler_exists,
                "features_file": features_exists,
                "output_directory": OUTPUT_DIR.exists()
            },
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": str(e)
        }


# === CLI INTERFACE ===

def main():
    """CLI pentru testare locală"""
    import argparse

    parser = argparse.ArgumentParser(description='Win Probability Model API')
    parser.add_argument('command', choices=['evaluate', 'predict', 'health'],
                        help='Command to execute')
    parser.add_argument('--match-id', type=int, help='Match ID for prediction')
    parser.add_argument('--output', default='console', choices=['console', 'json'],
                        help='Output format')

    args = parser.parse_args()

    if args.command == 'health':
        result = health_check()

    elif args.command == 'evaluate':
        result = evaluate_model_full(save_json=True)

    elif args.command == 'predict':
        if not args.match_id:
            print("Error: --match-id required for predict command")
            sys.exit(1)

        model_wrapper = WinProbabilityModel()
        model_wrapper.load_model()
        result = model_wrapper.predict_match(args.match_id)

    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

    # Output
    if args.output == 'json':
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("=" * 80)


if __name__ == "__main__":
    main()
