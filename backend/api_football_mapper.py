"""
Mapare date din API-Football la formatul MatchInput al modelului
"""
from typing import Optional, List, Dict
from models import ApiFootballPredictionInput, MatchInput, MatchEvent


def _obj_get(obj, key, default=None):
    """Acces compatibil pentru dict sau obiect Pydantic."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _extract_stat_value(stats_list: List[Dict], stat_type: str, alternate_types: List[str] = None) -> float:
    """
    Extrage valoare dintr-o lista de statistici API-Football

    Args:
        stats_list: Lista de {"type": "...", "value": ...} din API-Football
        stat_type: Tipul statisticii de cautat
        alternate_types: Alte tipuri echivalente (ex: ["xG", "Expected Goals"])

    Returns:
        Valoarea extrasa sau 0 daca nu gasit
    """
    search_types = [stat_type]
    if alternate_types:
        search_types.extend(alternate_types)

    for stat in stats_list:
        if _obj_get(stat, "type") in search_types:
            value = _obj_get(stat, "value")

            if isinstance(value, str) and value.endswith("%"):
                try:
                    return float(value.rstrip("%"))
                except ValueError:
                    return 0.0

            if isinstance(value, dict):
                return float(value.get("total", 0))

            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0

    return 0.0


def _count_cards_from_events(events: List, team_id: int, card_type: str) -> int:
    """
    Numara cartonase din lista de evenimente
    """
    count = 0
    for event in events:
        team = _obj_get(event, "team", {}) or {}
        team_event_id = _obj_get(team, "id")
        if (team_event_id == team_id and
            _obj_get(event, "type") == "Card" and
                _obj_get(event, "detail") == card_type):
            count += 1
    return count


def _extract_minute(time_dict: Optional[Dict]) -> int:
    """
    Extrage minutul dintr-un obiect de timp API-Football
    """
    if not time_dict:
        return 0

    elapsed = time_dict.get("elapsed", 0)
    extra = time_dict.get("extra", 0)

    if extra:
        return min(120, elapsed + extra)
    return min(120, elapsed or 0)


def _extract_scores_from_fixture(fixture) -> tuple[int, int]:
    """Extrage scorul preferand score.fulltime, cu fallback pe goals."""
    score_obj = _obj_get(fixture, "score", {}) or {}
    fulltime = _obj_get(score_obj, "fulltime", {}) or {}

    ft_home = _obj_get(fulltime, "home")
    ft_away = _obj_get(fulltime, "away")

    if ft_home is not None and ft_away is not None:
        return int(ft_home), int(ft_away)

    goals_obj = _obj_get(fixture, "goals", {}) or {}
    goals_home = _obj_get(goals_obj, "home", 0)
    goals_away = _obj_get(goals_obj, "away", 0)

    return int(goals_home or 0), int(goals_away or 0)


def _convert_api_events_to_match_events(events: List, home_team_id: int) -> List[MatchEvent]:
    """
    Converteste API-Football events la MatchEvent format
    """
    match_events = []

    for event in events:
        try:
            minute = _extract_minute(_obj_get(event, "time"))
            event_type = (_obj_get(event, "type", "") or "").lower()
            team = _obj_get(event, "team", {}) or {}
            player = _obj_get(event, "player", {}) or {}
            team_id = _obj_get(team, "id")
            team_name = _obj_get(team, "name", "")
            player_name = _obj_get(player, "name", "")
            detail = _obj_get(event, "detail", "")
            comments = _obj_get(event, "comments", "")

            # Determina daca e home sau away
            is_home = "home" if team_id == home_team_id else "away"

            # Mapare tip de event
            if event_type == "goal":
                match_events.append(MatchEvent(
                    minute=minute,
                    event_type="goal",
                    team=is_home,
                    player=player_name,
                    additional_info=comments or ""
                ))

            elif event_type == "card" and detail:
                if "Yellow" in detail:
                    match_events.append(MatchEvent(
                        minute=minute,
                        event_type="yellow_card",
                        team=is_home,
                        player=player_name,
                        additional_info=comments or ""
                    ))
                elif "Red" in detail:
                    match_events.append(MatchEvent(
                        minute=minute,
                        event_type="red_card",
                        team=is_home,
                        player=player_name,
                        additional_info=comments or ""
                    ))

            elif event_type in ["subst", "substitution"]:
                match_events.append(MatchEvent(
                    minute=minute,
                    event_type="substitution",
                    team=is_home,
                    player=player_name,
                    additional_info=comments or ""
                ))

            elif event_type == "injury":
                match_events.append(MatchEvent(
                    minute=minute,
                    event_type="injury",
                    team=is_home,
                    player=player_name,
                    additional_info=comments or ""
                ))

        except Exception as e:
            print(f"Eroare la procesare event: {e}")
            continue

    # Sorteaza dupa minut
    match_events.sort(key=lambda e: e.minute)
    return match_events


def map_api_football_to_match_input(api_input: ApiFootballPredictionInput) -> MatchInput:
    """
    Mapare date API-Football la MatchInput pentru predictie
    """
    fixture = api_input.fixture
    statistics = api_input.statistics
    events = api_input.events or []

    # Validari
    if not fixture or not fixture.goals:
        raise ValueError("Fixture sau goals lipsesc din input")

    if len(statistics) != 2:
        raise ValueError("Trebuie exact 2 echipe in statistics")

    # Extract team IDs
    home_team = fixture.teams.get("home", {})
    away_team = fixture.teams.get("away", {})
    home_team_id = home_team.get("id")
    away_team_id = away_team.get("id")
    
    # Extract team names early for logging
    home_team_name = home_team.get("name") or "Home Team"
    away_team_name = away_team.get("name") or "Away Team"

    if not home_team_id or not away_team_id:
        raise ValueError("Team IDs lipsesc din fixture")

    # Extract statistics for each team
    home_stats = None
    away_stats = None

    for stat_entry in statistics:
        team = _obj_get(stat_entry, "team", {}) or {}
        team_id = _obj_get(team, "id")
        stats = _obj_get(stat_entry, "statistics", [])
        if team_id == home_team_id:
            home_stats = stats
        elif team_id == away_team_id:
            away_stats = stats

    if not home_stats or not away_stats:
        raise ValueError("Statistics lipsesc pentru una dintre echipe")

    # Extract minute - din fixture.elapsed
    minute = fixture.elapsed or 0
    minute = min(120, max(0, minute))

    # Extract scores
    score_home, score_away = _extract_scores_from_fixture(fixture)

    # Extract statistics
    shots_home = int(_extract_stat_value(home_stats, "Total Shots", ["Shots"]))
    shots_away = int(_extract_stat_value(away_stats, "Total Shots", ["Shots"]))

    shots_on_target_home = int(_extract_stat_value(
        home_stats, "Shots on Goal", ["Shots on Target"]))
    shots_on_target_away = int(_extract_stat_value(
        away_stats, "Shots on Goal", ["Shots on Target"]))

    passes_home = int(_extract_stat_value(
        home_stats, "Total passes", ["Total Passes", "Passes"]))
    passes_away = int(_extract_stat_value(
        away_stats, "Total passes", ["Total Passes", "Passes"]))

    # Possession percentage
    possession_home = _extract_stat_value(
        home_stats, "Ball Possession", ["Possession"])
    possession_away = _extract_stat_value(
        away_stats, "Ball Possession", ["Possession"])

    # xG (Expected Goals)
    xg_home = _extract_stat_value(home_stats, "expected_goals", ["Expected Goals", "xG"])
    xg_away = _extract_stat_value(away_stats, "expected_goals", ["Expected Goals", "xG"])
    
    # Log extracted stats for verification
    print(f"[MAPPER] HOME TEAM: {home_team_name}")
    print(f"  Shots: {shots_home} (on target: {shots_on_target_home})")
    print(f"  Passes: {passes_home}")
    print(f"  xG: {xg_home}")
    print(f"  Possession: {possession_home}%")
    print(f"[MAPPER] AWAY TEAM: {away_team_name}")
    print(f"  Shots: {shots_away} (on target: {shots_on_target_away})")
    print(f"  Passes: {passes_away}")
    print(f"  xG: {xg_away}")
    print(f"  Possession: {possession_away}%")

    # Cards from events
    yellow_home = _count_cards_from_events(events, home_team_id, "Yellow Card")
    yellow_away = _count_cards_from_events(events, away_team_id, "Yellow Card")
    red_home = _count_cards_from_events(events, home_team_id, "Red Card")
    red_away = _count_cards_from_events(events, away_team_id, "Red Card")

    print(f"[MAPPER] CARDS FROM EVENTS:")
    print(f"  HOME: {yellow_home}Y {red_home}R")
    print(f"  AWAY: {yellow_away}Y {red_away}R")

    # Generate match_id daca nu e dat
    match_id = api_input.match_id or f"fixture_{fixture.id}"

    # Converteste events
    match_events = _convert_api_events_to_match_events(events, home_team_id)
    print(f"[MAPPER] EVENTS PROCESSED: {len(match_events)} events converted from {len(events)} API events")

    # Construieste MatchInput
    match_input = MatchInput(
        match_id=match_id,
        minute=minute,
        score_home=score_home,
        score_away=score_away,
        xg_home=xg_home,
        xg_away=xg_away,
        shots_home=shots_home,
        shots_away=shots_away,
        shots_on_target_home=shots_on_target_home,
        shots_on_target_away=shots_on_target_away,
        passes_home=passes_home,
        passes_away=passes_away,
        pressure_home=possession_home,
        pressure_away=possession_away,
        yellow_cards_home=yellow_home,
        yellow_cards_away=yellow_away,
        red_cards_home=red_home,
        red_cards_away=red_away,
        is_home_team=1,
        under_pressure=0,
        counterpress=0,
        events=match_events,
        teams={
            "home": {
                "id": home_team.get("id"),
                "name": home_team_name,
                "logo": home_team.get("logo"),
            },
            "away": {
                "id": away_team.get("id"),
                "name": away_team_name,
                "logo": away_team.get("logo"),
            },
        },
    )

    print(f"Mapare API-Football completata: {match_id}")
    print(f"[MAPPER] ====== FINAL MATCH INPUT FOR MODEL ======")
    print(f"  Match ID: {match_id}")
    print(f"  Minute: {minute}")
    print(f"  Score: {score_home}-{score_away}")
    print(f"  xG: {xg_home}-{xg_away}")
    print(f"  Shots: {shots_home} ({shots_on_target_home} on target) vs {shots_away} ({shots_on_target_away} on target)")
    print(f"  Passes: {passes_home} vs {passes_away}")
    print(f"  Possession: {possession_home}% vs {possession_away}%")
    print(f"  Cards: HOME {yellow_home}Y/{red_home}R | AWAY {yellow_away}Y/{red_away}R")
    print(f"  Events: {len(match_events)} processed")
    print(f"  Teams: {home_team_name} vs {away_team_name}")
    print(f"===========================================")

    return match_input
