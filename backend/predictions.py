"""
Prediction Service - Apel model ML si salvare rezultate
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import numpy as np
import pandas as pd
import joblib

from config import MODEL_PATH, MODEL_DIR
from users import UserManager
from models import PredictionResponse, MatchInput


class PredictionService:
    """Service pentru predictii - load model, predict, save"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.model_loaded = False
        self._load_model()

    def _load_model(self):
        """
        Incarca modelul ML (LightGBM Pipeline).
        """
        try:
            self.model = joblib.load(str(MODEL_PATH))
            # LightGBM Pipeline nu folosește scaler extern
            self.scaler = None
            self.feature_cols = self._extract_feature_cols(self.model)
            if not self.feature_cols:
                raise ValueError(
                    "Nu am putut determina lista de features din model")
            self.model_loaded = True
            print("Model ML incarcat cu succes")
            print(f"[PREDICTION_SERVICE] Model path: {MODEL_PATH}")
            print(
                f"[PREDICTION_SERVICE] Loaded model={type(self.model).__name__} "
                f"(no external scaler) features={len(self.feature_cols)}"
            )
            print(f"[PREDICTION_SERVICE] Feature columns: {list(self.feature_cols)}")
        except Exception as e:
            print(f"Eroare la incarcarea modelului: {e}")
            self.model_loaded = False

    @staticmethod
    def _extract_feature_cols(model) -> List[str]:
        """Extrage numele features in ordinea de antrenare din model/pipeline."""
        estimator = model
        if hasattr(model, "steps"):
            estimator = model.steps[-1][1]

        for attr in ("feature_name_", "feature_names_in_"):
            names = getattr(estimator, attr, None)
            if names is not None:
                return [str(c) for c in list(names)]

        # Fallback pe pipeline
        names = getattr(model, "feature_names_in_", None)
        if names is not None:
            return [str(c) for c in list(names)]
        return []

    @staticmethod
    def _rolling_mean_last3(history: List[Optional[float]]) -> float:
        """Media pe fereastra de 3 valori (ignorare None), ca rolling(3).mean()."""
        window = [v for v in history[-3:] if v is not None]
        return float(np.mean(window)) if window else 0.0

    def predict(self, match_input: MatchInput) -> Optional[Dict]:
        """
        Efectueaza predictie pentru o situatie de meci

        Args:
            match_input: MatchInput cu feature-urile evenimentului

        Returns:
            PredictionResponse dict sau None daca eroare
        """
        if not self.model_loaded:
            print("[PREDICTION_SERVICE] Model not loaded. Aborting prediction.")
            return None

        try:
            print(
                f"[PREDICTION_SERVICE] ========== PREDICTION START =========="
            )
            print(
                f"[PREDICTION_SERVICE] match_id={match_input.match_id} "
                f"minute={match_input.minute} events={len(match_input.events)}"
            )
            print(
                f"[PREDICTION_SERVICE] Input Data:"
                f"\n  Score: HOME {match_input.score_home}-{match_input.score_away} AWAY"
                f"\n  xG: HOME {match_input.xg_home}-{match_input.xg_away} AWAY"
                f"\n  Shots: HOME {match_input.shots_home} ({match_input.shots_on_target_home} on target) | AWAY {match_input.shots_away} ({match_input.shots_on_target_away} on target)"
                f"\n  Passes: HOME {match_input.passes_home} | AWAY {match_input.passes_away}"
                f"\n  Pressure: HOME {match_input.pressure_home}% | AWAY {match_input.pressure_away}%"
                f"\n  Cards: HOME {match_input.yellow_cards_home}Y {match_input.red_cards_home}R | AWAY {match_input.yellow_cards_away}Y {match_input.red_cards_away}R"
                f"\n  Match Flags: is_home_team={match_input.is_home_team} under_pressure={match_input.under_pressure} counterpress={match_input.counterpress}"
            )

            # Construieste feature vector
            feature_vector = self._build_feature_vector(match_input)

            if feature_vector is None:
                print("[PREDICTION_SERVICE] Feature vector generation failed.")
                return None

            print(
                f"[PREDICTION_SERVICE] Feature vector constructed: {len(feature_vector)} features"
                f"\n  Values: {[round(float(v), 4) for v in feature_vector]}"
            )

            # Construieste DataFrame cu nume de coloane 
            input_df = pd.DataFrame(
                [feature_vector], columns=self.feature_cols)
            print(
                f"[PREDICTION_SERVICE] Feature columns: {list(self.feature_cols)}"
            )

            # Predictie
            print(f"[PREDICTION_SERVICE] Running {type(self.model).__name__} (LightGBM) model...")
            y_pred = self.model.predict(input_df)[0]
            y_proba = self.model.predict_proba(input_df)[0]

            # Maparea rezultatului
            outcome_map = {0: "away_win", 1: "draw", 2: "home_win"}
            predicted_outcome = outcome_map[y_pred]

            print(
                f"[PREDICTION_SERVICE] Model output:"
                f"\n  Raw prediction: {y_pred} ({predicted_outcome})"
                f"\n  Probabilities: away_win={y_proba[0]:.4f} draw={y_proba[1]:.4f} home_win={y_proba[2]:.4f}"
                f"\n  Confidence: {float(np.max(y_proba)):.4f}"
            )

            # Response
            key_events = []
            match_insights = {}

            if match_input.events and len(match_input.events) > 0:
                key_events, match_insights = self._analyze_match_timeline(
                    match_input)

            prediction = {
                "match_id": match_input.match_id,
                "minute": match_input.minute,
                "prediction_time": datetime.utcnow().isoformat(),
                "score_home": int(match_input.score_home),
                "score_away": int(match_input.score_away),
                "final_score": f"{int(match_input.score_home)}-{int(match_input.score_away)}",
                "probabilities": {
                    "away_win": float(y_proba[0]),
                    "draw": float(y_proba[1]),
                    "home_win": float(y_proba[2])
                },
                "confidence": float(np.max(y_proba)),
                "predicted_outcome": predicted_outcome,
                "teams": match_input.teams.model_dump() if match_input.teams is not None else None,
                "key_events": key_events,
                "match_insights": match_insights,
                # Date utile pentru audit/debug salvate in fisierul din matches/
                "_input_snapshot": match_input.model_dump(),
                "_model_execution": {
                    "model_class": type(self.model.steps[-1][1]).__name__ if hasattr(self.model, "steps") else type(self.model).__name__,
                    "pipeline_class": type(self.model).__name__,
                    "scaler_class": type(self.scaler).__name__ if self.scaler is not None else "none",
                    "feature_columns": [str(col) for col in self.feature_cols],
                    "feature_vector": [float(v) for v in feature_vector],
                    "generated_at": datetime.utcnow().isoformat(),
                }
            }

            print(
                f"[PREDICTION_SERVICE] PREDICTION COMPLETE"
                f"\n  Match: {prediction['final_score']}"
                f"\n  Outcome: {predicted_outcome}"
                f"\n  Probabilities: away={prediction['probabilities']['away_win']:.4f} draw={prediction['probabilities']['draw']:.4f} home={prediction['probabilities']['home_win']:.4f}"
                f"\n  Confidence: {prediction['confidence']:.4f}"
                f"\n========== PREDICTION END ==========="
            )

            return prediction

        except Exception as e:
            print(f"Eroare la predicție: {e}")
            return None

    def _build_feature_vector(self, match_input: MatchInput) -> Optional[List]:
        """Construieste feature vector din input - suporta si snapshot static si timeline de evenimente"""
        try:
            # Start cu stats din input 
            cumulative_stats = {
                "score_home": match_input.score_home,
                "score_away": match_input.score_away,
                "xg_home": match_input.xg_home,
                "xg_away": match_input.xg_away,
                "shots_home": match_input.shots_home,
                "shots_away": match_input.shots_away,
                "shots_on_target_home": match_input.shots_on_target_home,
                "shots_on_target_away": match_input.shots_on_target_away,
                "passes_home": match_input.passes_home,
                "passes_away": match_input.passes_away,
                "yellow_cards_home": match_input.yellow_cards_home,
                "yellow_cards_away": match_input.yellow_cards_away,
                "red_cards_home": match_input.red_cards_home,
                "red_cards_away": match_input.red_cards_away,
                "pressure_home": match_input.pressure_home,
                "pressure_away": match_input.pressure_away,
            }

            # IMPORTANT: Daca exista events, MERGE event counters (goals, cards) in cumulative_stats
            # Stats majore (shots, passes, xG, pressure) raman asa cum sunt din input
            if match_input.events and len(match_input.events) > 0:
                event_counters = self._process_event_counters(
                    match_input.events, match_input.minute)
                # Update DOAR counters din events, pastreaza alte stats din input
                cumulative_stats["score_home"] = event_counters["score_home"]
                cumulative_stats["score_away"] = event_counters["score_away"]
                cumulative_stats["yellow_cards_home"] = event_counters["yellow_cards_home"]
                cumulative_stats["yellow_cards_away"] = event_counters["yellow_cards_away"]
                cumulative_stats["red_cards_home"] = event_counters["red_cards_home"]
                cumulative_stats["red_cards_away"] = event_counters["red_cards_away"]
                print(f"✓ Events: {len(match_input.events)} procesat(e)")
                print(
                    f"  Score (updated): {cumulative_stats['score_home']}-{cumulative_stats['score_away']}")
                print(
                    f"  Stats (from input): shots {cumulative_stats['shots_home']}-{cumulative_stats['shots_away']}, passes {cumulative_stats['passes_home']}-{cumulative_stats['passes_away']}")

            # max_minute = momentul final al meciului (extra time inclus in events)
            event_minutes = [e.minute for e in (match_input.events or [])]
            max_minute = max([match_input.minute] + event_minutes + [1])

            # Snapshot de final de meci: momentum ≈ 0 (scorul/xG/posesia sunt
            # stabile la fluierul final, iar score_diff final este oricum prezent
            # explicit ca feature). Momentum-ul pe secventa se calculeaza in
            # analiza timeline pentru detectarea momentelor decisive.
            return self._vector_from_state(
                minute=match_input.minute,
                cumulative_stats=cumulative_stats,
                is_home_team=match_input.is_home_team,
                under_pressure=match_input.under_pressure,
                counterpress=match_input.counterpress,
                max_minute=max_minute,
                momentum=None,
            )

        except Exception as e:
            print(f"Eroare la build feature vector: {e}")
            return None

    def _vector_from_state(
        self,
        minute: int,
        cumulative_stats: Dict,
        is_home_team: int,
        under_pressure: int,
        counterpress: int,
        max_minute: Optional[int] = None,
        momentum: Optional[Dict] = None,
    ) -> Optional[List]:
        """Construieste feature vector pentru o stare de joc data.

        Vectorul se construieste generic, dupa lista de features a modelului
        incarcat, deci se adapteaza automat daca modelul se schimba.
        """
        try:
            # max_minute folosit pentru time_remaining; protejat de impartirea la 0
            if max_minute is None or max_minute <= 0:
                max_minute = max(int(minute), 1)

            momentum = momentum or {}

            score_home = cumulative_stats.get("score_home", 0)
            score_away = cumulative_stats.get("score_away", 0)
            score_diff = score_home - score_away

            xg_home = cumulative_stats.get("xg_home", 0.0)
            xg_away = cumulative_stats.get("xg_away", 0.0)
            xg_diff = xg_home - xg_away

            pressure_home = cumulative_stats.get("pressure_home", 0)
            pressure_away = cumulative_stats.get("pressure_away", 0)

            yellow_diff = cumulative_stats.get(
                "yellow_cards_home", 0) - cumulative_stats.get("yellow_cards_away", 0)
            red_diff = cumulative_stats.get(
                "red_cards_home", 0) - cumulative_stats.get("red_cards_away", 0)
            cards_diff = yellow_diff + red_diff * 2

            time_remaining = max(0, max_minute - minute)
            time_remaining_norm = time_remaining / max_minute if max_minute else 0.0

            # Maparea numelor features la valori (inclusiv cele derivate)
            values = {
                # Base (24)
                "minute": minute,
                "timestamp_seconds": minute * 60,
                "score_home": score_home,
                "score_away": score_away,
                "score_diff": score_diff,
                "red_cards_home": cumulative_stats.get("red_cards_home", 0),
                "red_cards_away": cumulative_stats.get("red_cards_away", 0),
                "yellow_cards_home": cumulative_stats.get("yellow_cards_home", 0),
                "yellow_cards_away": cumulative_stats.get("yellow_cards_away", 0),
                "cards_diff": cards_diff,
                "xg_home": xg_home,
                "xg_away": xg_away,
                "xg_diff": xg_diff,
                "shots_home": cumulative_stats.get("shots_home", 0),
                "shots_away": cumulative_stats.get("shots_away", 0),
                "shots_on_target_home": cumulative_stats.get("shots_on_target_home", 0),
                "shots_on_target_away": cumulative_stats.get("shots_on_target_away", 0),
                "passes_home": cumulative_stats.get("passes_home", 0),
                "passes_away": cumulative_stats.get("passes_away", 0),
                "pressure_home": pressure_home,
                "pressure_away": pressure_away,
                "is_home_team": is_home_team,
                "under_pressure": under_pressure,
                "counterpress": counterpress,
                # Derived - momentum (0 implicit; calculate pe secventa in timeline)
                "score_momentum": float(momentum.get("score_momentum", 0.0)),
                "xg_momentum": float(momentum.get("xg_momentum", 0.0)),
                "pressure_momentum": float(momentum.get("pressure_momentum", 0.0)),
                # Derived - context temporal
                "time_remaining": time_remaining,
                "time_remaining_norm": time_remaining_norm,
                "is_late_game": 1 if minute > 75 else 0,
                "is_early_game": 1 if minute < 30 else 0,
                "is_crunch_time": 1 if abs(score_diff) <= 1 else 0,
                # Derived - context de joc
                "is_winning": 1 if score_diff > 0 else 0,
                "score_xg_gap": score_diff - xg_diff,
                "pressure_advantage": pressure_home - pressure_away,
            }

            # Compatibilitate cu eventuale features vechi (pass accuracy) daca apar
            if "passes_accuracy_home" not in values:
                passes_h = cumulative_stats.get("passes_home", 0)
                values["passes_accuracy_home"] = min(
                    0.9, passes_h / max(passes_h + 20, 1))
            if "passes_accuracy_away" not in values:
                passes_a = cumulative_stats.get("passes_away", 0)
                values["passes_accuracy_away"] = min(
                    0.9, passes_a / max(passes_a + 20, 1))

            features = [values.get(col, 0) for col in self.feature_cols]

            return features if len(features) == len(self.feature_cols) else None
        except Exception as e:
            print(f"Eroare la construire vector: {e}")
            return None

    def _predict_probabilities_for_state(
        self,
        minute: int,
        cumulative_stats: Dict,
        is_home_team: int,
        under_pressure: int,
        counterpress: int,
        max_minute: Optional[int] = None,
        momentum: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Ruleaza modelul pe o stare intermediara si returneaza probabilitatile."""
        feature_vector = self._vector_from_state(
            minute=minute,
            cumulative_stats=cumulative_stats,
            is_home_team=is_home_team,
            under_pressure=under_pressure,
            counterpress=counterpress,
            max_minute=max_minute,
            momentum=momentum,
        )
        if feature_vector is None:
            return None

        input_df = pd.DataFrame([feature_vector], columns=self.feature_cols)
        # Pipeline LightGBM
        probs = self.model.predict_proba(input_df)[0]
        pred = self.model.predict(input_df)[0]
        outcome_map = {0: "away_win", 1: "draw", 2: "home_win"}

        return {
            "away_win": float(probs[0]),
            "draw": float(probs[1]),
            "home_win": float(probs[2]),
            "predicted_outcome": outcome_map[pred],
        }

    def _analyze_match_timeline(self, match_input: MatchInput) -> tuple[list, dict]:
        """
        Detecteaza momente decisive
        """
        try:
            sorted_events = sorted(
                [e for e in match_input.events if e.minute <= match_input.minute],
                key=lambda e: e.minute,
            )
            if not sorted_events:
                return [], {"timeline_points": 0, "message": "No events available for decisive moments."}

            counters = {
                "score_home": 0,
                "score_away": 0,
                "yellow_cards_home": 0,
                "yellow_cards_away": 0,
                "red_cards_home": 0,
                "red_cards_away": 0,
                "shots_home": 0,
                "shots_away": 0,
                "shots_on_target_home": 0,
                "shots_on_target_away": 0,
                "passes_home": 0,
                "passes_away": 0,
                "pressure_home": 0,
                "pressure_away": 0,
            }

            timeline = []
            prev_probs = None

            max_minute = max(
                [match_input.minute] + [e.minute for e in sorted_events] + [1])

            # Tracking pentru momentum
            prev_score_diff = None
            prev_xg_diff = None
            prev_pressure_home = None
            xg_diff_diffs: List[Optional[float]] = []
            pressure_diffs: List[Optional[float]] = []

            for event in sorted_events:
                team_side = "home" if event.team.lower() == "home" else "away"
                evt = event.event_type.lower()

                if evt == "goal":
                    counters[f"score_{team_side}"] += 1
                    counters[f"shots_{team_side}"] += 1
                    counters[f"shots_on_target_{team_side}"] += 1
                elif evt == "yellow_card":
                    counters[f"yellow_cards_{team_side}"] += 1
                elif evt == "red_card":
                    counters[f"red_cards_{team_side}"] += 1
                elif evt == "shot":
                    counters[f"shots_{team_side}"] += 1
                    if "on-target" in (event.additional_info or "").lower():
                        counters[f"shots_on_target_{team_side}"] += 1
                elif evt == "pass":
                    counters[f"passes_{team_side}"] += 1
                elif evt == "pressure":
                    counters[f"pressure_{team_side}"] += 1

                progress = max(0.05, min(1.0, event.minute / max_minute))
                state = {
                    "score_home": counters["score_home"],
                    "score_away": counters["score_away"],
                    "xg_home": match_input.xg_home * progress,
                    "xg_away": match_input.xg_away * progress,
                    "shots_home": max(counters["shots_home"], int(round(match_input.shots_home * progress))),
                    "shots_away": max(counters["shots_away"], int(round(match_input.shots_away * progress))),
                    "shots_on_target_home": max(counters["shots_on_target_home"], int(round(match_input.shots_on_target_home * progress))),
                    "shots_on_target_away": max(counters["shots_on_target_away"], int(round(match_input.shots_on_target_away * progress))),
                    "passes_home": max(counters["passes_home"], int(round(match_input.passes_home * progress))),
                    "passes_away": max(counters["passes_away"], int(round(match_input.passes_away * progress))),
                    "pressure_home": max(float(counters["pressure_home"]), float(match_input.pressure_home * progress)),
                    "pressure_away": max(float(counters["pressure_away"]), float(match_input.pressure_away * progress)),
                    "yellow_cards_home": counters["yellow_cards_home"],
                    "yellow_cards_away": counters["yellow_cards_away"],
                    "red_cards_home": counters["red_cards_home"],
                    "red_cards_away": counters["red_cards_away"],
                }

                # Momentum pe secventa
                score_diff_now = state["score_home"] - state["score_away"]
                xg_diff_now = state["xg_home"] - state["xg_away"]
                pressure_home_now = state["pressure_home"]

                score_momentum = 0.0 if prev_score_diff is None else (
                    score_diff_now - prev_score_diff)

                xg_diff_diffs.append(
                    None if prev_xg_diff is None else (xg_diff_now - prev_xg_diff))
                xg_momentum = self._rolling_mean_last3(xg_diff_diffs)

                pressure_diffs.append(
                    None if prev_pressure_home is None else (pressure_home_now - prev_pressure_home))
                pressure_momentum = self._rolling_mean_last3(pressure_diffs)

                prev_score_diff = score_diff_now
                prev_xg_diff = xg_diff_now
                prev_pressure_home = pressure_home_now

                probs = self._predict_probabilities_for_state(
                    minute=event.minute,
                    cumulative_stats=state,
                    is_home_team=match_input.is_home_team,
                    under_pressure=match_input.under_pressure,
                    counterpress=match_input.counterpress,
                    max_minute=max_minute,
                    momentum={
                        "score_momentum": score_momentum,
                        "xg_momentum": xg_momentum,
                        "pressure_momentum": pressure_momentum,
                    },
                )
                if probs is None:
                    continue

                impact_home = 0.0 if prev_probs is None else probs["home_win"] - \
                    prev_probs["home_win"]
                impact_draw = 0.0 if prev_probs is None else probs["draw"] - \
                    prev_probs["draw"]
                impact_away = 0.0 if prev_probs is None else probs["away_win"] - \
                    prev_probs["away_win"]
                abs_impact = max(abs(impact_home), abs(
                    impact_draw), abs(impact_away))

                direction = "home"
                if abs(impact_draw) == abs_impact:
                    direction = "draw"
                if abs(impact_away) == abs_impact:
                    direction = "away"

                timeline.append({
                    "minute": int(event.minute),
                    "event_type": event.event_type,
                    "team": event.team,
                    "player": event.player,
                    "description": event.additional_info,
                    "score": f"{state['score_home']}-{state['score_away']}",
                    "probabilities": {
                        "away_win": probs["away_win"],
                        "draw": probs["draw"],
                        "home_win": probs["home_win"],
                    },
                    "impact_home": float(impact_home),
                    "impact_draw": float(impact_draw),
                    "impact_away": float(impact_away),
                    "abs_impact": float(abs_impact),
                    "impact_direction": direction,
                })

                prev_probs = probs

            if not timeline:
                return [], {"timeline_points": 0, "message": "Timeline analysis failed."}

            # Criterii decisive
            decisive = []
            for point in timeline:
                evt = point["event_type"].lower()
                is_goal = evt == "goal"
                is_red = evt == "red_card"
                is_penalty = "penalty" in (
                    point.get("description") or "").lower()
                is_shot_important = evt == "shot" and point["abs_impact"] > 0.02
                is_substitution = evt == "substitution" and point["abs_impact"] > 0.015
                is_other_decisive = point["abs_impact"] > 0.03

                if is_goal or is_red or is_penalty or is_shot_important or is_substitution or is_other_decisive:
                    before_home = point["probabilities"]["home_win"] - \
                        point["impact_home"]
                    before_draw = point["probabilities"]["draw"] - \
                        point["impact_draw"]
                    before_away = point["probabilities"]["away_win"] - \
                        point["impact_away"]

                    point["description_nlp"] = (
                        f"{point['event_type']} ({point['team']}) la min {point['minute']}: "
                        f"Home {before_home:.1%}->{point['probabilities']['home_win']:.1%}, "
                        f"Draw {before_draw:.1%}->{point['probabilities']['draw']:.1%}, "
                        f"Away {before_away:.1%}->{point['probabilities']['away_win']:.1%}. "
                        f"Impact max {point['abs_impact']:.1%} ({point['impact_direction']})."
                    )
                    decisive.append(point)

            decisive_sorted = sorted(
                decisive, key=lambda x: x["abs_impact"], reverse=True)
            key_events = decisive_sorted[:10]

            insights = {
                "timeline_points": len(timeline),
                "decisive_moments_count": len(decisive_sorted),
                "goals_detected": len([p for p in timeline if p["event_type"].lower() == "goal"]),
                "red_cards_detected": len([p for p in timeline if p["event_type"].lower() == "red_card"]),
                "yellow_cards_detected": len([p for p in timeline if p["event_type"].lower() == "yellow_card"]),
                "max_impact": float(decisive_sorted[0]["abs_impact"]) if decisive_sorted else 0.0,
                "max_impact_minute": int(decisive_sorted[0]["minute"]) if decisive_sorted else None,
                "timeline": timeline,
            }

            print(
                f"[PREDICTION_SERVICE] Decisive moments computed: {len(decisive_sorted)} "
                f"(returned top {len(key_events)})"
            )

            return key_events, insights
        except Exception as e:
            print(f"[PREDICTION_SERVICE] Timeline analysis failed: {e}")
            return [], {"timeline_points": 0, "error": str(e)}

    def _process_event_counters(self, events: List, target_minute: int) -> Dict:
        """
        Procesa DOAR event counters (goals, cards) din timeline

        Args:
            events: Lista de MatchEvent in ordine cronologica
            target_minute: Pana la ce minut calculez

        Returns:
            Dict cu DOAR counters actualizati din events
        """
        counters = {
            "score_home": 0,
            "score_away": 0,
            "yellow_cards_home": 0,
            "yellow_cards_away": 0,
            "red_cards_home": 0,
            "red_cards_away": 0,
        }

        try:
            sorted_events = sorted(events, key=lambda e: e.minute)

            for event in sorted_events:
                if event.minute > target_minute:
                    break

                is_home = event.team.lower() == "home"
                home_or_away = "home" if is_home else "away"

                # Procesa DOAR goal și card events
                if event.event_type.lower() == "goal":
                    counters[f"score_{home_or_away}"] += 1

                elif event.event_type.lower() == "yellow_card":
                    counters[f"yellow_cards_{home_or_away}"] += 1

                elif event.event_type.lower() == "red_card":
                    counters[f"red_cards_{home_or_away}"] += 1

            return counters

        except Exception as e:
            print(f"✗ Eroare la procesare event counters: {e}")
            return counters

    def _process_event_timeline(self, events: List, target_minute: int) -> Dict:
        """
        Procesa timeline de evenimente si calculeaza stats cumulative pana la target_minute

        Args:
            events: Lista de MatchEvent in ordine cronologica
            target_minute: Pana la ce minut calculez aggregatele

        Returns:
            Dict cu stats cumulative (score_home, shots_home, passes_home, cards, etc)
        """
        cumulative = {
            "score_home": 0,
            "score_away": 0,
            "xg_home": 0.0,
            "xg_away": 0.0,
            "shots_home": 0,
            "shots_away": 0,
            "shots_on_target_home": 0,
            "shots_on_target_away": 0,
            "passes_home": 0,
            "passes_away": 0,
            "yellow_cards_home": 0,
            "yellow_cards_away": 0,
            "red_cards_home": 0,
            "red_cards_away": 0,
            "pressure_home": 0,
            "pressure_away": 0,
        }

        try:
            # Sorteaza eventurile dupa minut
            sorted_events = sorted(events, key=lambda e: e.minute)

            for event in sorted_events:
                # Opreste daca am depasit target_minute
                if event.minute > target_minute:
                    break

                # Determina echipa
                is_home = event.team.lower() == "home"
                home_or_away = "home" if is_home else "away"

                # Procesa dupa tip de eveniment
                if event.event_type.lower() == "goal":
                    cumulative[f"score_{home_or_away}"] += 1
                    # Implicit include o mica parte de xG (pentru logica)
                    cumulative[f"xg_{home_or_away}"] += 0.5

                elif event.event_type.lower() == "shot":
                    cumulative[f"shots_{home_or_away}"] += 1
                    # Presupun ca din descriere putem extrage daca e on-target
                    if "on-target" in (event.additional_info or "").lower():
                        cumulative[f"shots_on_target_{home_or_away}"] += 1

                elif event.event_type.lower() == "pass":
                    cumulative[f"passes_{home_or_away}"] += 1

                elif event.event_type.lower() == "yellow_card":
                    cumulative[f"yellow_cards_{home_or_away}"] += 1

                elif event.event_type.lower() == "red_card":
                    cumulative[f"red_cards_{home_or_away}"] += 1

                elif event.event_type.lower() == "pressure":
                    cumulative[f"pressure_{home_or_away}"] += 1

            print(
                f" Timeline procesat: {len(sorted_events)} events pana la min {target_minute}")
            print(
                f"  Home: {cumulative['score_home']}-{cumulative['score_away']} Away")
            return cumulative

        except Exception as e:
            print(f"✗ Eroare la procesare timeline: {e}")
            return cumulative  # Returneaza partial daca este o eroare

    def save_prediction(self, user_id: str, prediction: Dict) -> bool:
        """Salveaza predictie in fisier user"""
        try:
            match_id = prediction.get("match_id")
            matches_dir = UserManager.matches_dir(user_id)
            matches_dir.mkdir(parents=True, exist_ok=True)

            match_file = matches_dir / f"{match_id}.json"

            with open(match_file, 'w') as f:
                json.dump(prediction, f, indent=2)

            print(
                f"[PREDICTION_SERVICE] Prediction saved at: {match_file.resolve()}")

            # Incrementeaza counter
            UserManager.update_prediction_count(user_id, 1)
            print(
                f"[PREDICTION_SERVICE] Prediction counter incremented for user_id={user_id}")

            return True
        except Exception as e:
            print(f"Eroare la salvare predicție: {e}")
            return False

    def get_user_predictions(self, user_id: str) -> List[Dict]:
        """Returneaza toate predictiile unui user"""
        try:
            matches_dir = UserManager.matches_dir(user_id)
            predictions = []

            if not matches_dir.exists():
                return predictions

            for match_file in matches_dir.glob("*.json"):
                try:
                    with open(match_file, 'r') as f:
                        prediction = json.load(f)
                        predictions.append(prediction)
                except:
                    pass

            return sorted(predictions, key=lambda x: x.get("prediction_time", ""), reverse=True)

        except Exception as e:
            print(f"Eroare la citire predictii: {e}")
            return []

    def get_prediction(self, user_id: str, match_id: str) -> Optional[Dict]:
        """Returneaza o predictie specifica"""
        try:
            match_file = UserManager.matches_dir(user_id) / f"{match_id}.json"

            if match_file.exists():
                with open(match_file, 'r') as f:
                    return json.load(f)

            return None
        except:
            return None

    def get_prediction_by_fixture_id(self, user_id: str, fixture_id: int) -> Optional[Dict]:
        """
        Cauta predictie pentru un fixture_id specific.
        
        Fiindcă predictiile se salveaza cu match_id = f"fixture_{fixture_id}",
        aceasta functie cauta dupa fixture_id.
        """
        try:
            match_id = f"fixture_{fixture_id}"
            return self.get_prediction(user_id, match_id)
        except:
            return None


# Instanta globala a service-ului
prediction_service = PredictionService()
