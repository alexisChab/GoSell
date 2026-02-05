import os
from datetime import timedelta

class Config:
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.environ.get("JWT_ACCESS_EXPIRES_MIN", "15")))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get("JWT_REFRESH_EXPIRES_DAYS", "30")))
