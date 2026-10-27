from flask import Blueprint

from utils.helpers import utc_now

system_bp = Blueprint('system', __name__)


@system_bp.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(utc_now())}


@system_bp.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}
