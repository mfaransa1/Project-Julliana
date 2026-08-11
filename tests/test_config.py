import importlib.util
from pathlib import Path

import pytest


CONFIG_PATH = Path(__file__).resolve().parents[1] / "ChatbotWebsite" / "config.py"
spec = importlib.util.spec_from_file_location("juliana_config", CONFIG_PATH)
assert spec and spec.loader
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

ConfigurationError = config.ConfigurationError
ProductionConfig = config.ProductionConfig
get_config = config.get_config


class CompleteProductionConfig(ProductionConfig):
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    MAIL_ENABLED = False


class IncompleteProductionConfig(ProductionConfig):
    SECRET_KEY = None
    SQLALCHEMY_DATABASE_URI = None
    MAIL_ENABLED = False


def test_production_configuration_requires_a_secret_and_database_url():
    with pytest.raises(ConfigurationError, match="SECRET_KEY"):
        IncompleteProductionConfig.validate()


def test_complete_production_configuration_is_accepted():
    CompleteProductionConfig.validate()


def test_unknown_environment_is_rejected():
    with pytest.raises(ConfigurationError, match="Unsupported JULIANA_ENV"):
        get_config("unsupported")
