"""Shared fixtures for application-level tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def app():
    # Keep the existing pure-Python checks runnable when optional web packages
    # have intentionally not been installed in a lightweight environment.
    from ChatbotWebsite import create_app, db
    from ChatbotWebsite.config import TestingConfig

    class AppTestConfig(TestingConfig):
        SECRET_KEY = "test-only-secret"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
        ADMIN_USERNAMES = frozenset({"admin"})
        MAIL_ENABLED = False

    application = create_app(AppTestConfig)
    with application.app_context():
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make_user(username="alice", email="alice@example.com", password="safe-password"):
        from ChatbotWebsite import bcrypt, db
        from ChatbotWebsite.models import User

        with app.app_context():
            user = User(
                username=username,
                email=email,
                password=bcrypt.generate_password_hash(password).decode("utf-8"),
            )
            db.session.add(user)
            db.session.commit()
            return user.id

    return _make_user


def login(client, email="alice@example.com", password="safe-password"):
    """Authenticate through the public route, exercising form validation."""
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
