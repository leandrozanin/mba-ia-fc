import logging
import os
import secrets

logger = logging.getLogger(__name__)

VERSAO_API = "1.0.0"


def _env_bool(nome, padrao):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "on")


def _env_lista(nome):
    return [item.strip() for item in os.environ.get(nome, "").split(",") if item.strip()]


def load_settings(overrides=None):
    """Carrega a configuração do ambiente; nenhum segredo fica versionado."""
    settings = {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        "DATABASE_PATH": os.environ.get("DATABASE_PATH", "loja.db"),
        "DEBUG": _env_bool("DEBUG", False),
        "HOST": os.environ.get("HOST", "127.0.0.1"),
        "PORT": int(os.environ.get("PORT", "5000")),
        "CORS_ORIGINS": _env_lista("CORS_ORIGINS"),
        "AMBIENTE": os.environ.get("APP_ENV", "desenvolvimento"),
        "SEED_DEMO_DATA": _env_bool("SEED_DEMO_DATA", True),
        "SEED_USER_PASSWORD": os.environ.get("SEED_USER_PASSWORD"),
        "ALLOW_DB_RESET": _env_bool("ALLOW_DB_RESET", False),
    }
    settings.update(overrides or {})

    if not settings["SECRET_KEY"]:
        settings["SECRET_KEY"] = secrets.token_hex(32)
        logger.warning("SECRET_KEY não definida; usando chave aleatória temporária.")
    return settings
