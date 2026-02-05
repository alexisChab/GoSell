from flask import g
from sqlalchemy.orm import Session

def db() -> Session:
    return g.db
