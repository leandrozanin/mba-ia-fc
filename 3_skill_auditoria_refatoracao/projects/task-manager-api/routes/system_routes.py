from datetime import datetime

from flask import Blueprint

from config.settings import API_VERSION

system_bp = Blueprint('system', __name__)


@system_bp.get('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.now())}


@system_bp.get('/')
def index():
    return {'message': 'Task Manager API', 'version': API_VERSION}
