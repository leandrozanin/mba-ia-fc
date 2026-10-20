import os
from datetime import datetime, timezone
from flask import Flask
from flask_cors import CORS
from database import db
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///tasks.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.environ.get('SECRET_KEY') or os.urandom(32).hex(),
    )
    if test_config:
        app.config.update(test_config)
    CORS(app)
    db.init_app(app)
    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Recurso não encontrado'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Erro interno'}, 500

    with app.app_context():
        db.create_all()
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', '').lower() == 'true', host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
