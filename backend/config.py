"""
Configuratie Backend - Win Probability Prediction API
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
USERS_DIR = DATA_DIR / "users"
MODEL_DIR = Path(__file__).parent.parent / \
    "model_3_clase"  # Relatia cu model_3_clase

# Creaza directoare daca nu exista
USERS_DIR.mkdir(parents=True, exist_ok=True)

# JWT Configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY", "your-secret-key-change-in-production-12345678")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Model Configuration
MODEL_PATH = MODEL_DIR / "experimentare" / "lgbm_final_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler_3class.pkl"
FEATURES_PATH = MODEL_DIR / "feature_cols.pkl"

# API Configuration
API_VERSION = "1.0.0"
API_TITLE = "Win Probability Prediction API"
API_DESCRIPTION = "Backend pentru predictii probabilistiche in-game in fotbal"

# API-Football Configuration
API_FOOTBALL_BASE_URL = os.getenv(
    "API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
API_FOOTBALL_KEY = os.getenv(
    "API_FOOTBALL_KEY", os.getenv("VITE_API_FOOTBALL_KEY", ""))
SUPERLIGA_LEAGUE_ID = int(os.getenv("SUPERLIGA_LEAGUE_ID", "283"))
SUPERLIGA_CACHE_SECONDS = int(os.getenv("SUPERLIGA_CACHE_SECONDS", "3600"))

# RapidAPI Configuration
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "api-football-v1.p.rapidapi.com")

# Logging
LOG_LEVEL = "INFO"
