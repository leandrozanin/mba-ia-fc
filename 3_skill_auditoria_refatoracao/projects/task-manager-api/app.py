import logging

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import load_config
from controllers.errors import AppError
from database import db
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.auth_service import AuthService

logger = logging.getLogger(__name__)


def _register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        if isinstance(err, HTTPException):
            return err
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500


def create_app(overrides=None):
    config = load_config(overrides)

    app = Flask(__name__)
    app.config.update(config)

    if config['CORS_ORIGINS']:
        CORS(app, origins=config['CORS_ORIGINS'])
    db.init_app(app)
    app.extensions['auth_service'] = AuthService(config['SECRET_KEY'], config['TOKEN_MAX_AGE'])

    for blueprint in (system_bp, task_bp, user_bp, category_bp, report_bp):
        app.register_blueprint(blueprint)
    _register_error_handlers(app)

    with app.app_context():
        db.create_all()
    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    application = create_app()
    application.run(
        debug=application.config['RUN_DEBUG'],
        host=application.config['RUN_HOST'],
        port=application.config['RUN_PORT'],
    )
