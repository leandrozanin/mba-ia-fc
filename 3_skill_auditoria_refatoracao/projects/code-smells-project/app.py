"""Composition root: monta a aplicação a partir de config, models, rotas e middlewares."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from middlewares.error_handler import register_error_handlers
from models import database
from views.routes import bp


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_mapping(load_settings(overrides))

    if app.config["CORS_ORIGINS"]:
        CORS(app, origins=app.config["CORS_ORIGINS"])

    database.init_app(app)
    register_error_handlers(app)
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = create_app()
    logging.getLogger(__name__).info("Servidor em http://%s:%s", app.config["HOST"], app.config["PORT"])
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
