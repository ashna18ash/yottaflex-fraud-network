from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Find the project root folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Database folder
DATABASE_DIR = PROJECT_ROOT / "database"

# Create the database folder if it does not exist
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database file
DATABASE_PATH = DATABASE_DIR / "fraud_network.db"

# SQLite connection URL
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# Create database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for database models
Base = declarative_base()