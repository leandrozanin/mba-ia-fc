from flask import Flask
from flask_cors import CORS

from .config import load_config, validate_config
from .db import close_db, init_db
from .errors import register_error_handlers
from .notificacoes import NotificadorLog
from .routes import pedidos, produtos, relatorios, sistema, usuarios


def create_app(overrides=None):
    config = load_config()
    config.update(overrides or {})
    validate_config(config)

    app = Flask(__name__)
    app.config.update(config)

    init_db(app.config)
    app.teardown_appcontext(close_db)
    register_error_handlers(app)

    if app.config["CORS_ORIGINS"]:
        CORS(app, origins=app.config["CORS_ORIGINS"])

    app.extensions["notificador"] = config.get("NOTIFICADOR") or NotificadorLog()

    for modulo in (sistema, produtos, usuarios, pedidos, relatorios):
        app.register_blueprint(modulo.bp)

    return app
