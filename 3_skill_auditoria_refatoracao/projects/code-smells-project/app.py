from flask import Flask, jsonify
from flask_cors import CORS
from config.settings import Settings
from database import get_db
from middlewares.error_handler import register_error_handlers
from views.routes import register_routes


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Settings)
    if test_config:
        app.config.update(test_config)
    CORS(app)
    register_routes(app)
    register_error_handlers(app)

    @app.post('/admin/query')
    def disabled_admin_query():
        return jsonify({'erro': 'Endpoint desabilitado'}), 410

    @app.post('/admin/reset-db')
    def disabled_database_reset():
        return jsonify({'erro': 'Operação administrativa desabilitada'}), 403
    @app.get('/')
    def index():
        return jsonify({'mensagem': 'Bem-vindo à API da Loja', 'versao': '1.0.0',
                        'endpoints': {'produtos': '/produtos', 'usuarios': '/usuarios',
                                      'pedidos': '/pedidos', 'login': '/login',
                                      'relatorios': '/relatorios/vendas', 'health': '/health'}})
    return app

app = create_app()

if __name__ == '__main__':
    get_db()
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
