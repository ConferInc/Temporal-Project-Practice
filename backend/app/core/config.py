import os

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:temporal@postgres:5432/temporal")

# Temporal
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
