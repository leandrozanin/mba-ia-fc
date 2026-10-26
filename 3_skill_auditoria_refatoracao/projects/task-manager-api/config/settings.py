import logging
import os
import secrets

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

API_VERSION = '1.0'


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def load_settings(overrides=None):
    """Configuração vinda do ambiente (e de um .env local, se existir); nenhum segredo fica versionado."""
    load_dotenv()
    settings = {
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///tasks.db'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': _env_bool('DEBUG', False),
        'HOST': os.environ.get('HOST', '127.0.0.1'),
        'PORT': int(os.environ.get('PORT', '5000')),
        'CORS_ORIGINS': [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip()],
        'TOKEN_MAX_AGE_SECONDS': int(os.environ.get('TOKEN_MAX_AGE_SECONDS', str(8 * 3600))),
        'SMTP_HOST': os.environ.get('SMTP_HOST'),
        'SMTP_PORT': int(os.environ.get('SMTP_PORT', '587')),
        'SMTP_USER': os.environ.get('SMTP_USER'),
        'SMTP_PASSWORD': os.environ.get('SMTP_PASSWORD'),
        'SEED_USER_PASSWORD': os.environ.get('SEED_USER_PASSWORD'),
    }
    settings.update(overrides or {})

    if not settings['SECRET_KEY']:
        settings['SECRET_KEY'] = secrets.token_hex(32)
        logger.warning('SECRET_KEY não definida; usando chave aleatória temporária (tokens expiram no restart).')
    return settings
