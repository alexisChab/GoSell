import pytest

from dotenv import load_dotenv, find_dotenv
from app import create_app
from datetime import timedelta
from app.extensions import db
import os
from app.models.token_blocklist import TokenBlocklist

@pytest.fixture(scope="session")
def app():
    load_dotenv(find_dotenv())
    app = create_app()
    app.config.update(
        TESTING=True,
        WT_COOKIE_SECURE=False,
        JWT_COOKIE_CSRF_PROTECT=False,
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=5),
        JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=7),
        JWT_TOKEN_LOCATION=["cookies"],
        SQLALCHEMY_DATABASE_URI=os.environ["DATABASE_URL"]
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    return app

@pytest.fixture(autouse=True)
def clean_token_blocklist(app):
    with app.app_context():
        db.session.query(TokenBlocklist).delete()
        db.session.commit()
    yield
@pytest.fixture()
def client(app):
    return app.test_client()
