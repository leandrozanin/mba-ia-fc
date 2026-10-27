import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.constants import ADMIN_ROLE, DEFAULT_ROLE
from utils.helpers import utc_now

# Hashes gravados pela versão anterior (MD5 hex, sem salt); migrados no próximo login.
_LEGACY_MD5 = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        if self.has_legacy_password():
            legacy = hashlib.md5(pwd.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, pwd)

    def has_legacy_password(self):
        return bool(self.password and _LEGACY_MD5.match(self.password))

    def is_admin(self):
        return self.role == ADMIN_ROLE
