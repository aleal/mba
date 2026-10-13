import os
import secrets


def _bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def _lista(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


class Settings:
    """Configuração lida de variáveis de ambiente, com defaults seguros para desenvolvimento."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool("FLASK_DEBUG")
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    SEED_DEMO_DATA = _bool("SEED_DEMO_DATA", "true")
    SEED_ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "")

    CORS_ORIGINS = _lista("CORS_ORIGINS", "http://localhost:5000")

    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    ENABLE_ADMIN_RESET = _bool("ENABLE_ADMIN_RESET")
    ENABLE_ADMIN_QUERY = _bool("ENABLE_ADMIN_QUERY")

    APP_VERSION = "1.0.0"
    APP_ENV = os.environ.get("APP_ENV", "desenvolvimento")
