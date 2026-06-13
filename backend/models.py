"""
Pydantic Models pentru validare request/response
"""
from pydantic import BaseModel, EmailStr, Field, AliasChoices
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

# AUTH MODELS

class UserRegister(BaseModel):
    """Model pentru inregistrare"""
    email: EmailStr
    password: str = Field(..., min_length=8,
                          description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "secure123456",
                "full_name": "Ion Popescu"
            }
        }


class UserLogin(BaseModel):
    """Model pentru login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """JWT Token payload data"""
    user_id: str
    email: str
    exp: datetime

# === USER MODELS ===


class UserResponse(BaseModel):
    """User info response (no password!)"""
    user_id: str
    email: str
    full_name: str
    created_at: datetime
    total_predictions: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "email": "user@example.com",
                "full_name": "Ion Popescu",
                "created_at": "2026-03-29T10:00:00Z",
                "total_predictions": 5
            }
        }

# PREDICTION MODELS


class TeamInfo(BaseModel):
    """Echipa implicata in meci"""
    id: Optional[int] = None
    name: str
    logo: Optional[str] = None


class MatchTeams(BaseModel):
    """Structura echipelor in payload/response"""
    home: TeamInfo
    away: TeamInfo


class MatchEvent(BaseModel):
    """Un eveniment din meci"""
    minute: int = Field(..., ge=0, le=120, description="Minutul evenimentului")
    event_type: str = Field(
        ..., description="goal|yellow_card|red_card|substitution|injury|pass|shot")
    team: str = Field(...,
                      description="home|away - echipa care a efectuat evenimentul")
    player: str = Field(default="", description="Jucatorul implicat")
    additional_info: str = Field(
        default="", description="Detalii suplimentare")

    class Config:
        json_schema_extra = {
            "example": {
                "minute": 12,
                "event_type": "goal",
                "team": "home",
                "player": "Grozav",
                "additional_info": "Gol din actiune dupa o trecere de Bodea"
            }
        }


class MatchInput(BaseModel):
    """Model pentru match data - folosit intern de mapper si prediction service"""
    minute: int = Field(..., ge=0, le=120)
    events: List[MatchEvent] = Field(
        default=[], description="Timeline de evenimente")
    score_home: int = Field(..., ge=0)
    score_away: int = Field(..., ge=0)
    xg_home: float = Field(..., ge=0)
    xg_away: float = Field(..., ge=0)
    shots_home: int = Field(..., ge=0)
    shots_away: int = Field(..., ge=0)
    shots_on_target_home: int = Field(..., ge=0)
    shots_on_target_away: int = Field(..., ge=0)
    passes_home: int = Field(..., ge=0)
    passes_away: int = Field(..., ge=0)
    pressure_home: float = Field(..., ge=0, le=100)
    pressure_away: float = Field(..., ge=0, le=100)
    red_cards_home: int = Field(default=0, ge=0)
    red_cards_away: int = Field(default=0, ge=0)
    yellow_cards_home: int = Field(default=0, ge=0)
    yellow_cards_away: int = Field(default=0, ge=0)
    is_home_team: int = Field(default=1, ge=0, le=1)
    under_pressure: int = Field(default=0, ge=0, le=1)
    counterpress: int = Field(default=0, ge=0, le=1)
    match_id: str = Field(..., description="Unique match identifier")
    teams: Optional[MatchTeams] = Field(default=None)


class PredictionResponse(BaseModel):
    """Response din predictie"""
    match_id: str
    minute: int
    prediction_time: datetime
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    final_score: Optional[str] = None
    probabilities: Dict[str, float]
    confidence: float 
    predicted_outcome: str 
    teams: Optional[MatchTeams] = None
    key_events: Optional[List[Dict]] = []
    match_insights: Optional[Dict] = {}
    input_snapshot: Optional[Dict] = Field(
        default=None,
        alias="_input_snapshot",
        description="Snapshot complet al inputului folosit la predictie"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "match_id": "match_12345",
                "minute": 45,
                "prediction_time": "2026-03-29T11:30:00Z",
                "score_home": 2,
                "score_away": 1,
                "final_score": "2-1",
                "probabilities": {
                    "away_win": 0.25,
                    "draw": 0.30,
                    "home_win": 0.45
                },
                "confidence": 0.45,
                "predicted_outcome": "home_win",
                "teams": {
                    "home": {"id": 645, "name": "Farul Constanta", "logo": None},
                    "away": {"id": 674, "name": "FCSB", "logo": None}
                },
                "key_events": [],
                "match_insights": {},
                "_input_snapshot": {
                    "match_id": "match_12345",
                    "minute": 45,
                    "score_home": 2,
                    "score_away": 1
                }
            }
        }


class MatchHistory(BaseModel):
    """Istoric predictii user"""
    user_id: str
    match_id: str
    home_team: str
    away_team: str
    prediction_time: datetime
    final_prediction: Dict[str, float]
    actual_result: Optional[str] = None
    accuracy: Optional[bool] = None 

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "match_id": "match_12345",
                "home_team": "FCSB",
                "away_team": "CFR Cluj",
                "prediction_time": "2026-03-29T11:30:00Z",
                "final_prediction": {"away_win": 0.25, "draw": 0.30, "home_win": 0.45},
                "actual_result": "home_win",
                "accuracy": True
            }
        }

# ERROR MODELS


class ErrorResponse(BaseModel):
    """Standard error response"""
    status: str = "error"
    message: str
    details: Optional[Dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Invalid credentials",
                "details": None
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    model_loaded: bool
    database_available: bool

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2026-03-29T11:30:00Z",
                "model_loaded": True,
                "database_available": True
            }
        }


# API-FOOTBALL DATA MODELS


class ApiFootballTeam(BaseModel):
    """Team data from API-Football"""
    id: int
    name: str
    logo: Optional[str] = None


class ApiFootballFixture(BaseModel):
    """Fixture data from API-Football"""
    id: int
    timestamp: Optional[int] = None
    date: Optional[str] = None
    status: Optional[Dict] = None
    elapsed: Optional[int] = None
    venue: Optional[Dict] = None
    referee: Optional[str] = None
    goals: Dict = Field(default={"home": 0, "away": 0})
    score: Optional[Dict] = None
    teams: Dict = Field(default={"home": {}, "away": {}})


class ApiFootballStatistic(BaseModel):
    """Individual statistic"""
    type: str
    value: Optional[Dict | int | str | float] = None


class ApiFootballTeamStats(BaseModel):
    """Team statistics from API-Football"""
    team: ApiFootballTeam
    statistics: List[ApiFootballStatistic] = []


class ApiFootballEvent(BaseModel):
    """Event from API-Football """
    time: Dict 
    team: ApiFootballTeam
    player: Dict = Field(default={"id": None, "name": None})
    type: str 
    detail: Optional[str] = None 
    comments: Optional[str] = None


class ApiFootballPredictionInput(BaseModel):
    """
    Input pentru predictie pe baza datelor brute din API-Football

    """
    fixture: ApiFootballFixture
    statistics: List[ApiFootballTeamStats] 
    events: List[ApiFootballEvent] = Field(
        default=[], description="Timeline de evenimente din meci")
    match_id: str = Field(
        default="", description="Custom match ID. Dacă nu e dat, se generate din fixture ID")

    class Config:
        json_schema_extra = {
            "example": {
                "fixture": {
                    "id": 1152476,
                    "timestamp": 1711795200,
                    "date": "2026-03-29T18:00:00Z",
                    "status": {"short": "1H"},
                    "elapsed": 45,
                    "goals": {"home": 2, "away": 1},
                    "teams": {
                        "home": {"id": 645, "name": "Farul Constanta"},
                        "away": {"id": 674, "name": "FCSB"}
                    }
                },
                "statistics": [
                    {
                        "team": {"id": 645, "name": "Farul Constanta"},
                        "statistics": [
                            {"type": "Shots", "value": 12},
                            {"type": "Shots on Goal", "value": 5},
                            {"type": "Total Passes", "value": 425},
                            {"type": "Ball Possession", "value": "58%"},
                            {"type": "Expected Goals", "value": 1.8}
                        ]
                    },
                    {
                        "team": {"id": 674, "name": "FCSB"},
                        "statistics": [
                            {"type": "Shots", "value": 8},
                            {"type": "Shots on Goal", "value": 3},
                            {"type": "Total Passes", "value": 380},
                            {"type": "Ball Possession", "value": "42%"},
                            {"type": "Expected Goals", "value": 0.9}
                        ]
                    }
                ],
                "events": [
                    {
                        "time": {"elapsed": 12},
                        "team": {"id": 645, "name": "Farul Constanta"},
                        "player": {"id": 123, "name": "Grozav"},
                        "type": "Goal",
                        "detail": None
                    }
                ],
                "match_id": "fixture_1152476"
            }
        }


# FIXTURES LISTING MODELS


class FixtureSummary(BaseModel):
    """Summary al unui meci din Superliga pentru afisare in lista"""
    fixture_id: int
    date: datetime
    home_team: str
    away_team: str
    home_logo: Optional[str] = None
    away_logo: Optional[str] = None
    status: str 
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    has_prediction: bool = False 
    prediction_minute: Optional[int] = None
    predicted_home_win_prob: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "fixture_id": 1152476,
                "date": "2026-03-29T18:00:00Z",
                "home_team": "Farul Constanta",
                "away_team": "FCSB",
                "status": "finished",
                "home_goals": 2,
                "away_goals": 1,
                "has_prediction": True,
                "prediction_minute": 45,
                "predicted_home_win_prob": 0.68
            }
        }


class FixturesListResponse(BaseModel):
    """Response pentru endpoint-ul cu lista meciurilor"""
    season: int
    league_id: int
    league_name: str
    total_fixtures: int
    fixtures: List[FixtureSummary]

    class Config:
        json_schema_extra = {
            "example": {
                "season": 2025,
                "league_id": 283,
                "league_name": "Superliga",
                "total_fixtures": 30,
                "fixtures": [
                    {
                        "fixture_id": 1152476,
                        "date": "2026-03-29T18:00:00Z",
                        "home_team": "Farul Constanta",
                        "away_team": "FCSB",
                        "status": "finished",
                        "home_goals": 2,
                        "away_goals": 1,
                        "has_prediction": True,
                        "prediction_minute": 45,
                        "predicted_home_win_prob": 0.68
                    }
                ]
            }
        }


class PredictionHistoryItem(BaseModel):
    """Un item din istoricul predictiilor user-ului"""
    prediction_id: str
    fixture_id: int
    date: datetime
    home_team: str
    away_team: str
    prediction_minute: int
    prediction_time: datetime
    p_home_win: float
    p_draw: float
    p_away_win: float
    predicted_outcome: str

    class Config:
        json_schema_extra = {
            "example": {
                "prediction_id": "pred_001",
                "fixture_id": 1152476,
                "date": "2026-03-29T18:00:00Z",
                "home_team": "Farul Constanta",
                "away_team": "FCSB",
                "prediction_minute": 45,
                "prediction_time": "2026-03-29T19:00:00Z",
                "p_home_win": 0.68,
                "p_draw": 0.22,
                "p_away_win": 0.10,
                "predicted_outcome": "home_win"
            }
        }


class PredictFixtureRequest(BaseModel):
    """Request pentru predictie pe baza fixture_id"""
    fixture_id: int = Field(...,
                            description="ID-ul fixture-ului din API-Football")

    class Config:
        json_schema_extra = {
            "example": {
                "fixture_id": 1152476
            }
        }
