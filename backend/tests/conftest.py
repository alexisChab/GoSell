import pytest

from dotenv import load_dotenv, find_dotenv
from app import create_app


@pytest.fixture()
def app():
    load_dotenv(find_dotenv())
    app = create_app()
    app.config.update(
        TESTING=True,
        WT_COOKIE_SECURE=False,
        JWT_COOKIE_CSRF_PROTECT=False,
    )
    return app


@pytest.fixture()
def client(app):
    return app.test_client()
