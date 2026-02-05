from flask import g
from app.db.session import SessionLocal

def init_request_db(app):
    @app.before_request
    def _open_db_session():
        g.db = SessionLocal()

    @app.teardown_request
    def _close_db_session(exc):
        db = getattr(g, "db", None)
        if db is None:
            return

        try:
            if exc:
                db.rollback()
            else:
                db.commit()
        finally:
            db.close()
