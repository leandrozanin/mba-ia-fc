"""Composition root: create_app() monta config, banco, serviços, rotas e middlewares."""
import logging

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  registra os models no metadata antes do create_all
from config.settings import load_settings
from database import db
from middlewares.auth import load_current_user
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_mapping(load_settings(overrides))

    if app.config['CORS_ORIGINS']:
        CORS(app, origins=app.config['CORS_ORIGINS'])

    db.init_app(app)
    app.extensions['notifier'] = NotificationService.from_config(app.config)
    app.before_request(load_current_user)
    register_error_handlers(app)

    for blueprint in (system_bp, task_bp, user_bp, report_bp, category_bp):
        app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()
    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    app = create_app()
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
