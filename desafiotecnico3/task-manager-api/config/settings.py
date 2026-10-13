import os
import secrets

from dotenv import load_dotenv

load_dotenv()  # carrega o .env (se existir) antes de ler as variáveis


def _env_bool(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


class Settings:
    """Configuração lida de variáveis de ambiente, com defaults seguros para desenvolvimento."""

    # Sem SECRET_KEY definida, gera uma aleatória por processo (tokens expiram a cada restart).
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = _env_bool('FLASK_DEBUG', False)
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    CORS_ORIGINS = [o.strip() for o in os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',') if o.strip()]
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    TOKEN_MAX_AGE_SECONDS = int(os.environ.get('TOKEN_MAX_AGE_SECONDS', str(8 * 60 * 60)))

    NOTIFICATIONS_ENABLED = _env_bool('NOTIFICATIONS_ENABLED', False)
    SMTP_HOST = os.environ.get('SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
