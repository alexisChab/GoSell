from flask import g
from sqlalchemy.orm import Session
from app.extensions import db as sa_db
def db() -> Session:
    if hasattr(g, "db"):
        return g.db
    return sa_db.session
