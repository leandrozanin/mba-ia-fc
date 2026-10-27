import os

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    pass


def _as_bool(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _as_list(value):
    return [item.strip() for item in (value or '').split(',') if item.strip()]


def load_config(overrides=None):
    """Monta a configuração a partir do ambiente (e de um .env local, se existir)."""
    load_dotenv()

    config = {
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///tasks.db'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'TOKEN_MAX_AGE': int(os.environ.get('TOKEN_MAX_AGE', 8 * 60 * 60)),
        'CORS_ORIGINS': _as_list(os.environ.get('CORS_ORIGINS')),
        'SMTP_HOST': os.environ.get('SMTP_HOST'),
        'SMTP_PORT': int(os.environ.get('SMTP_PORT', 587)),
        'SMTP_USER': os.environ.get('SMTP_USER'),
        'SMTP_PASSWORD': os.environ.get('SMTP_PASSWORD'),
        'RUN_DEBUG': _as_bool(os.environ.get('FLASK_DEBUG', 'false')),
        'RUN_HOST': os.environ.get('HOST', '127.0.0.1'),
        'RUN_PORT': int(os.environ.get('PORT', 5000)),
    }
    if overrides:
        config.update(overrides)

    if not config['SECRET_KEY']:
        raise ConfigError('SECRET_KEY não definida. Configure a variável de ambiente (veja .env.example).')
    return config
