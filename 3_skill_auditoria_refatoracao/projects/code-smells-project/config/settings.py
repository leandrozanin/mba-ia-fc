import os
import secrets

class Settings:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = os.environ.get('FLASK_DEBUG', '').lower() == 'true'
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'loja.db')
