import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs
from fastapi import FastAPI, Depends, HTTPException, Header, status, Request as FastAPIRequest
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional

from config import (
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    API_FOOTBALL_BASE_URL,
    API_FOOTBALL_KEY,
    SUPERLIGA_LEAGUE_ID,
    SUPERLIGA_CACHE_SECONDS,
)
from models import (
    UserRegister, UserLogin, Token, UserResponse,
    MatchInput, PredictionResponse, HealthResponse, ErrorResponse,
    ApiFootballPredictionInput, ApiFootballFixture, ApiFootballTeamStats, ApiFootballEvent,
    FixtureSummary, FixturesListResponse, PredictFixtureRequest
)
from auth import JWTHandler, PasswordHandler, extract_token_from_header
from users import UserManager
from predictions import prediction_service
from api_football_mapper import map_api_football_to_match_input

_superliga_cache = {
    "season": None,
    "fetched_at": None,
    "data": None,
}

# Cache pentru fixtures per season
_fixtures_cache = {
    "season": None,
    "fetched_at": None,
    "data": None,
}


def _is_cache_valid(cache_dict: dict, key_to_match: str = None, cache_seconds: int = SUPERLIGA_CACHE_SECONDS) -> bool:
    """
    Verifica daca cache este valid si expirat

    """
    if cache_dict.get("data") is None or cache_dict.get("fetched_at") is None:
        return False

    now = datetime.utcnow()
    time_diff = (now - cache_dict["fetched_at"]).total_seconds()

    return time_diff < cache_seconds


def _api_football_get(endpoint: str, query_params: dict) -> dict:
    """GET helper pentru API-Football cu handling consistent de erori."""
    if not API_FOOTBALL_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing API_FOOTBALL_KEY in backend environment"
        )

    query = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{API_FOOTBALL_BASE_URL}{endpoint}?{query}"

    request = Request(
        url,
        headers={"x-apisports-key": API_FOOTBALL_KEY},
        method="GET",
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = (
            "API-Football rate limit reached"
            if exc.code == 429
            else f"API-Football request failed ({exc.code})"
        )
        raise HTTPException(status_code=exc.code, detail=detail) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not connect to API-Football"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while calling API-Football"
        ) from exc

    errors = payload.get("errors")
    if errors:
        if isinstance(errors, dict):
            error_values = [str(v) for v in errors.values() if v]
        elif isinstance(errors, list):
            error_values = [str(v) for v in errors if v]
        else:
            error_values = [str(errors)]

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=", ".join(
                error_values) if error_values else "API-Football returned errors"
        )

    return payload


def _default_superliga_season() -> int:
    """Same logic as frontend: season starts in July."""
    now = datetime.utcnow()
    return now.year if now.month >= 7 else now.year - 1


# FASTAPI APP
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# === CORS Configuration ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: FastAPIRequest, exc: RequestValidationError):
    """Log detaliat pentru erorile 422 (inclusiv body) ca sa putem face debug la payload-ul."""
    try:
        raw_body = (await request.body()).decode("utf-8", errors="replace")
    except Exception:
        raw_body = "<unavailable>"

    print("[VALIDATION_ERROR] 422 Unprocessable Content")
    print(
        f"[VALIDATION_ERROR] path={request.url.path} method={request.method}")
    print(f"[VALIDATION_ERROR] errors={exc.errors()}")
    print(f"[VALIDATION_ERROR] body={raw_body}")

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# DEPENDENCY: Current User


async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extrage user_id din JWT token din Authorization header
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    token = extract_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>"
        )

    user_id = JWTHandler.decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = UserManager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user_id


# HEALTH CHECK

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "model_loaded": prediction_service.model_loaded,
        "database_available": True
    }


# SUPERLIGA ENDPOINTS

@app.get("/api/superliga/standings", response_model=list)
async def get_superliga_standings(season: Optional[int] = None):
    """
    Proxy pentru clasament Superliga cu API-Football.
    """
    if not API_FOOTBALL_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing API_FOOTBALL_KEY in backend environment"
        )

    selected_season = int(season or _default_superliga_season())
    now = datetime.utcnow()

    if (
        _superliga_cache["data"] is not None
        and _superliga_cache["season"] == selected_season
        and _superliga_cache["fetched_at"] is not None
        and (now - _superliga_cache["fetched_at"]).total_seconds() < SUPERLIGA_CACHE_SECONDS
    ):
        return _superliga_cache["data"]

    url = (
        f"{API_FOOTBALL_BASE_URL}/standings"
        f"?league={SUPERLIGA_LEAGUE_ID}&season={selected_season}"
    )

    request = Request(
        url,
        headers={
            "x-apisports-key": API_FOOTBALL_KEY,
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = (
            "API-Football rate limit reached"
            if exc.code == 429
            else f"API-Football request failed ({exc.code})"
        )
        raise HTTPException(status_code=exc.code, detail=detail) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not connect to API-Football"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while fetching standings"
        ) from exc

    errors = payload.get("errors")
    if errors:
        if isinstance(errors, dict):
            error_values = [str(v) for v in errors.values() if v]
        elif isinstance(errors, list):
            error_values = [str(v) for v in errors if v]
        else:
            error_values = [str(errors)]

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=", ".join(
                error_values) if error_values else "API-Football returned errors"
        )

    response_array = payload.get("response") or []
    if not response_array:
        return []

    standings_array = response_array[0].get(
        "league", {}).get("standings") or []
    if not standings_array:
        return []

    standings = [
        {
            "pozitie": team.get("rank"),
            "echipa": team.get("team", {}).get("name"),
            "meciuri": team.get("all", {}).get("played"),
            "victorii": team.get("all", {}).get("win"),
            "egaluri": team.get("all", {}).get("draw"),
            "infrangeri": team.get("all", {}).get("lose"),
            "goluriMarcate": team.get("all", {}).get("goals", {}).get("for"),
            "goluriPrimite": team.get("all", {}).get("goals", {}).get("against"),
            "golaveraj": team.get("goalsDiff"),
            "puncte": team.get("points"),
            "teamId": team.get("team", {}).get("id"),
            "logo": team.get("team", {}).get("logo"),
            "crest": team.get("team", {}).get("logo"),
            "form": team.get("form"),
            "status": team.get("status"),
            "description": team.get("description"),
            "group": team.get("group"),
        }
        for team in standings_array[0]
    ]

    _superliga_cache["season"] = selected_season
    _superliga_cache["fetched_at"] = now
    _superliga_cache["data"] = standings

    return standings


# AUTHENTICATION ENDPOINTS

@app.post("/auth/register", response_model=Token)
async def register(request: UserRegister):
    """
    Registrare user nou

    Returns: JWT token pentru noua utilizare
    """
    result = UserManager.create_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    user_id = result["user_id"]
    token_data = JWTHandler.create_access_token(
        user_id=user_id,
        email=request.email
    )

    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "expires_in": token_data["expires_in"]
    }


@app.post("/auth/login", response_model=Token)
async def login(request: UserLogin):
    """
    Login cu email si parola

    Returns: JWT token
    """
    user_id = UserManager.verify_credentials(
        email=request.email,
        password=request.password
    )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token_data = JWTHandler.create_access_token(
        user_id=user_id,
        email=request.email
    )

    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "expires_in": token_data["expires_in"]
    }


# USER ENDPOINTS

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(user_id: str = Depends(get_current_user)):
    """
    Returneaza profil utilizatorului curent

    Requires: JWT token în Authorization header
    """
    user_profile = UserManager.get_user_profile(user_id)

    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user_profile


# PREDICTION ENDPOINTS


# FIXTURES & PREDICTIONS LISTING ENDPOINTS

@app.get("/api/superliga/fixtures/{season}", response_model=FixturesListResponse)
async def get_superliga_fixtures(
    season: int,
    user_id: Optional[str] = Depends(get_current_user)
):
    """
    Returnează lista meciurilor din Superliga pentru sezonul selectat.

    Endpointul integreaza:
    1. Meciurile din API-Football pentru sezonul dat
    2. Verifica daca utilizatorul curent a generat predictii pentru fiecare meci
    3. Returneaza status, echipe si info predictie (daca exista)

    Query params:
    - season: Sezonul (ex: 2025, 2026)

    Returns: FixturesListResponse cu lista meciurilor + status predictii per user
    """
    print(f"[GET_FIXTURES] season={season} user_id={user_id}")

    if not API_FOOTBALL_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing API_FOOTBALL_KEY in backend environment"
        )

    now = datetime.utcnow()

    # Verifica cache pentru fixtures din sezonul solicitat
    if (
        _fixtures_cache["data"] is not None
        and _fixtures_cache["season"] == season
        and _fixtures_cache["fetched_at"] is not None
        and (now - _fixtures_cache["fetched_at"]).total_seconds() < SUPERLIGA_CACHE_SECONDS
    ):
        print(f"[GET_FIXTURES] Cache HIT for season {season}")
        fixtures_data = _fixtures_cache["data"]
    else:
        print(
            f"[GET_FIXTURES] Cache MISS for season {season} - fetching from API")

        # Fetch meciuri din API-Football
        url = (
            f"{API_FOOTBALL_BASE_URL}/fixtures"
            f"?league={SUPERLIGA_LEAGUE_ID}&season={season}"
        )

        request = Request(
            url,
            headers={"x-apisports-key": API_FOOTBALL_KEY},
            method="GET",
        )

        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"API-Football error: {str(exc)}"
            ) from exc

        fixtures_data = payload.get("response") or []
        print(f"[GET_FIXTURES] API returned {len(fixtures_data)} fixtures")
        if fixtures_data:
            print(
                f"[GET_FIXTURES] Sample fixture structure: {fixtures_data[0]}")

        # Store in cache
        _fixtures_cache["season"] = season
        _fixtures_cache["fetched_at"] = now
        _fixtures_cache["data"] = fixtures_data
        print(
            f"[GET_FIXTURES] Cached {len(fixtures_data)} fixtures for season {season}")

    # Conversie la FixtureSummary objects
    fixtures_list = []
    for fixture_obj in fixtures_data:
        fixture_id = fixture_obj.get("fixture", {}).get(
            "id") or fixture_obj.get("id")

        # Skip daca nu e fixture_id
        if not fixture_id:
            print(f"[GET_FIXTURES] Skipping fixture with no ID")
            continue

        # Extrage date
        fixture_info = fixture_obj.get("fixture", {})
        date_str = fixture_info.get("date") or fixture_obj.get("date")

        # Extrage status
        status_obj = fixture_info.get(
            "status") or fixture_obj.get("status") or {}
        status_short = status_obj.get("short", "NS") if isinstance(
            status_obj, dict) else "NS"

        # Extrage echipe
        teams_info = fixture_obj.get("teams", {})
        home_team_obj = teams_info.get("home") or {}
        away_team_obj = teams_info.get("away") or {}

        # Extrage goluri
        goals = fixture_obj.get("goals") or {}
        home_goals = goals.get("home")
        away_goals = goals.get("away")

        # Map status
        if status_short in ["1H", "2H", "ET", "P"]:
            status_mapped = "in_progress"
        elif status_short == "FT":
            status_mapped = "finished"
        else:
            status_mapped = "not_started"

        print(f"[GET_FIXTURES] fixture_id={fixture_id} date={date_str} "
              f"status={status_short}→{status_mapped} "
              f"score={home_goals}-{away_goals} "
              f"{home_team_obj.get('name', 'Unknown')} vs {away_team_obj.get('name', 'Unknown')}")

        # Verifica daca user-ul a facut predictie pentru acest meci
        user_prediction = None
        if user_id:
            user_prediction = prediction_service.get_prediction_by_fixture_id(
                user_id, fixture_id
            )

        fixture_summary = FixtureSummary(
            fixture_id=fixture_id,
            date=datetime.fromisoformat(date_str.replace(
                "Z", "+00:00")) if date_str else datetime.utcnow(),
            home_team=home_team_obj.get("name", "Unknown"),
            away_team=away_team_obj.get("name", "Unknown"),
            home_logo=home_team_obj.get("logo"),
            away_logo=away_team_obj.get("logo"),
            status=status_mapped,
            home_goals=home_goals,
            away_goals=away_goals,
            has_prediction=user_prediction is not None,
            prediction_minute=user_prediction.get(
                "minute") if user_prediction else None,
            predicted_home_win_prob=user_prediction.get("probabilities", {}).get(
                "home_win") if user_prediction else None
        )
        fixtures_list.append(fixture_summary)

    # Sort by date descending
    fixtures_list.sort(key=lambda x: x.date, reverse=True)

    response = FixturesListResponse(
        season=season,
        league_id=SUPERLIGA_LEAGUE_ID,
        league_name="Superliga",
        total_fixtures=len(fixtures_list),
        fixtures=fixtures_list
    )

    print(
        f"[GET_FIXTURES] Returning {len(fixtures_list)} fixtures for season {season}")
    return response


@app.post("/predict/by-fixture-id", response_model=PredictionResponse)
async def predict_by_fixture_id(
    request: PredictFixtureRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Predictie simplificata: primește doar fixture_id si fetch automat date din API-Football.

    Flux:
    1. Primeste fixture_id
    2. Fetch automat din /fixtures, /fixtures/statistics, /fixtures/events
    3. Mapeaza la MatchInput
    4. Ruleaza modelul
    5. Salveaza in istoric

    Requires: JWT token + fixture_id valid din API-Football
    """
    fixture_id = request.fixture_id
    print(f"[PREDICT/BY-FIXTURE-ID] user_id={user_id} fixture_id={fixture_id}")

    if not API_FOOTBALL_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing API_FOOTBALL_KEY"
        )

    try:
        # Fetch statistics (team info + stats)
        print(f"[PREDICT/BY-FIXTURE-ID] Step 1: Fetch statistics from /fixtures/statistics?fixture={fixture_id}")
        stats_payload = _api_football_get(
            f"/fixtures/statistics",
            {"fixture": str(fixture_id)}
        )
        stats_response = stats_payload.get("response") or []
        print(f"[PREDICT/BY-FIXTURE-ID]   Teams with stats: {len(stats_response)}")
        
        if len(stats_response) != 2:
            raise ValueError(f"Expected 2 teams in statistics, got {len(stats_response)}")
        
        for i, team_stats in enumerate(stats_response):
            team_info = team_stats.get("team", {})
            stats_list = team_stats.get("statistics", [])
            stat_types = {s.get("type"): s.get("value") for s in stats_list}
            print(f"[PREDICT/BY-FIXTURE-ID]   Team {i}: {team_info.get('name')} (id={team_info.get('id')})")
            print(f"[PREDICT/BY-FIXTURE-ID]     Key stats: Shots={stat_types.get('Total Shots')}, xG={stat_types.get('expected_goals')}, Passes={stat_types.get('Total passes')}, Possession={stat_types.get('Ball Possession')}")

        # Fetch events (cartonase, goluri, substituții)
        print(f"[PREDICT/BY-FIXTURE-ID] Step 2: Fetch events from /fixtures/events?fixture={fixture_id}")
        events_payload = _api_football_get(
            f"/fixtures/events",
            {"fixture": str(fixture_id)}
        )
        events_response = events_payload.get("response") or []
        print(f"[PREDICT/BY-FIXTURE-ID]   Total events: {len(events_response)}")
        
        # Group events by type si extrage info
        event_types = {}
        goals_home = 0
        goals_away = 0
        for event in events_response:
            event_type = event.get("type")
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Count goals per team
            if event_type == "Goal":
                team_id = event.get("team", {}).get("id")
                if team_id == stats_response[0].get("team", {}).get("id"):
                    goals_home += 1
                elif team_id == stats_response[1].get("team", {}).get("id"):
                    goals_away += 1
        
        print(f"[PREDICT/BY-FIXTURE-ID]   Event types: {event_types}")
        print(f"[PREDICT/BY-FIXTURE-ID]   Goals extracted: {goals_home}-{goals_away}")

        # Build fixture data from statistics and events
        print(f"[PREDICT/BY-FIXTURE-ID] Step 3: Constructing fixture data from statistics and events")
        fixture_data = {
            "id": fixture_id,
            "timestamp": None,
            "date": None,
            "status": {"short": "FT", "long": "Match Finished", "elapsed": 90},
            "elapsed": 90,
            "venue": None,
            "referee": None,
            "goals": {"home": goals_home, "away": goals_away},
            "score": {"home": goals_home, "away": goals_away},
            "teams": {
                "home": stats_response[0].get("team", {}),
                "away": stats_response[1].get("team", {})
            },
        }
        
        print(f"[PREDICT/BY-FIXTURE-ID]   Built fixture data: teams={fixture_data['teams']['home'].get('name')} vs {fixture_data['teams']['away'].get('name')}, score={goals_home}-{goals_away}")

        # Construct API input for mapper
        api_input = ApiFootballPredictionInput(
            fixture=ApiFootballFixture(**fixture_data),
            statistics=[ApiFootballTeamStats(**s) for s in stats_response],
            events=[ApiFootballEvent(**e) for e in events_response],
            match_id=f"fixture_{fixture_id}"
        )

        # Map to MatchInput
        match_input = map_api_football_to_match_input(api_input)

        print(f"[PREDICT/BY-FIXTURE-ID] Mapped to MatchInput: minute={match_input.minute} "
              f"score={match_input.score_home}-{match_input.score_away}")

        # Predict
        prediction = prediction_service.predict(match_input)
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Prediction failed"
            )

        # Add teams info to prediction
        if not prediction.get("teams"):
            home_team = fixture_data["teams"].get("home") or {}
            away_team = fixture_data["teams"].get("away") or {}
            prediction["teams"] = {
                "home": {
                    "id": home_team.get("id"),
                    "name": home_team.get("name"),
                    "logo": home_team.get("logo"),
                },
                "away": {
                    "id": away_team.get("id"),
                    "name": away_team.get("name"),
                    "logo": away_team.get("logo"),
                },
            }

        # Save prediction
        saved = prediction_service.save_prediction(user_id, prediction)

        print(f"[PREDICT/BY-FIXTURE-ID] Done: outcome={prediction.get('predicted_outcome')} "
              f"saved={saved}")

        return prediction

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid fixture data: {str(e)}"
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        ) from e


@app.get("/matches", response_model=list)
async def get_user_matches(user_id: str = Depends(get_current_user)):
    """
    Returneaza toate predictiile/meciurile pentru utilizatorul curent
    """
    print(f"[MATCHES] Incoming request user_id={user_id}")
    predictions = prediction_service.get_user_predictions(user_id)
    print(
        f"[MATCHES] Returning {len(predictions)} prediction(s) for user_id={user_id}")
    return predictions


@app.get("/matches/{match_id}", response_model=PredictionResponse, response_model_by_alias=True)
async def get_match_prediction(
    match_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Returneaza predictie specifica pentru un meci

    Requires: JWT token + match_id belongs to user
    """
    prediction = prediction_service.get_prediction(user_id, match_id)

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} not found for this user"
        )

    return prediction


@app.get("/")
async def root():
    """API info"""
    return {
        "api": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "status": "running"
    }
