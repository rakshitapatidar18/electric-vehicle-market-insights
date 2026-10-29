"""
Configuration settings for the Electric Vehicle Market Performance & Insights Project.
Provides centralized path management and default parameters.
"""

import os
from pathlib import Path

# Base directory (project root)
BASE_DIR = Path(__file__).resolve().parent

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# File paths
RAW_DATA_FILE = RAW_DATA_DIR / "electric_vehicles_raw.csv"
CLEANED_DATA_FILE = PROCESSED_DATA_DIR / "electric_vehicles_cleaned.csv"
TABLEAU_EXPORT_FILE = PROCESSED_DATA_DIR / "ev_tableau_export.csv"

# Database configuration
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "ev_market.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
SQL_QUERIES_PATH = DATABASE_DIR / "sql_queries.sql"

# Flask Application configuration
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ev-market-insights-secret-key-2026")
    DATABASE = str(DATABASE_PATH)
    # Tableau Public embed URL (set in environment variable or overridden here)
    TABLEAU_EMBED_URL = os.environ.get("TABLEAU_EMBED_URL", "")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
