"""Configuration loaded from the environment, never from source code."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class ConfigurationError(RuntimeError):
    """Raised when the application is started without required settings."""


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _database_url() -> str | None:
    """Read the new setting, with a temporary non-secret legacy alias."""
    return os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")


class Config:
    """Common settings shared by all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_ENABLED = _as_bool(os.getenv("MAIL_ENABLED"), default=False)
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = _as_bool(os.getenv("MAIL_USE_TLS"), default=True)
    MAIL_USE_SSL = _as_bool(os.getenv("MAIL_USE_SSL"), default=False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 3600

    LEARNING_CANDIDATES_ENABLED = _as_bool(
        os.getenv("LEARNING_CANDIDATES_ENABLED"), default=False
    )
    LEARNING_CONFIDENCE_THRESHOLD = float(
        os.getenv("LEARNING_CONFIDENCE_THRESHOLD", "0.60")
    )
    LEARNING_AUTO_TRAIN = _as_bool(os.getenv("LEARNING_AUTO_TRAIN"), default=False)
    LEARNING_TRAINING_THRESHOLD = int(
        os.getenv("LEARNING_TRAINING_THRESHOLD", "20")
    )

    @classmethod
    def validate(cls) -> None:
        """Validate only settings that are mandatory for the selected mode."""


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @classmethod
    def validate(cls) -> None:
        missing = [
            setting
            for setting in ("SECRET_KEY", "SQLALCHEMY_DATABASE_URI")
            if not getattr(cls, setting)
        ]
        if cls.MAIL_ENABLED:
            missing.extend(
                setting
                for setting in ("MAIL_SERVER", "MAIL_DEFAULT_SENDER")
                if not getattr(cls, setting)
            )
        if missing:
            raise ConfigurationError(
                "Production configuration is incomplete. Set: " + ", ".join(missing)
            )


def get_config(environment: str | None = None) -> type[Config]:
    """Return the configuration class selected by JULIANA_ENV."""

    selected = (environment or os.getenv("JULIANA_ENV", "development")).lower()
    configurations: dict[str, type[Config]] = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    try:
        return configurations[selected]
    except KeyError as error:
        raise ConfigurationError(
            "Unsupported JULIANA_ENV. Use development, testing, or production."
        ) from error
