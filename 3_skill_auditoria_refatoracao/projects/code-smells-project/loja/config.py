import os

TRUE_VALUES = {"1", "true", "yes", "on"}


def _bool_env(name, default=False):
    valor = os.environ.get(name)
    if valor is None:
        return default
    return valor.strip().lower() in TRUE_VALUES


def load_config():
    """Carrega a configuração do ambiente. Segredos nunca têm valor padrão."""
    origens = os.environ.get("CORS_ORIGINS", "")
    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        "DATABASE": os.environ.get("DATABASE_PATH", "loja.db"),
        "DEBUG": _bool_env("FLASK_DEBUG"),
        "HOST": os.environ.get("HOST", "127.0.0.1"),
        "PORT": int(os.environ.get("PORT", "5000")),
        "CORS_ORIGINS": [o.strip() for o in origens.split(",") if o.strip()],
        "TOKEN_MAX_AGE": int(os.environ.get("TOKEN_MAX_AGE", str(8 * 60 * 60))),
        "ENABLE_ADMIN_RESET": _bool_env("ENABLE_ADMIN_RESET"),
        "ADMIN_EMAIL": os.environ.get("ADMIN_EMAIL"),
        "ADMIN_PASSWORD": os.environ.get("ADMIN_PASSWORD"),
    }


def validate_config(config):
    if not config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY não configurada: defina a variável de ambiente SECRET_KEY.")
    if bool(config.get("ADMIN_EMAIL")) != bool(config.get("ADMIN_PASSWORD")):
        raise RuntimeError("Defina ADMIN_EMAIL e ADMIN_PASSWORD juntos para criar o administrador inicial.")
