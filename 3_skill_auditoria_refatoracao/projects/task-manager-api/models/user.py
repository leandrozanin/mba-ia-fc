import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.constants import ROLE_ADMIN, ROLE_USER
from utils.dates import utcnow

LEGACY_MD5_PATTERN = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    tasks = db.relationship('Task', back_populates='user')

    def to_dict(self):
        # O hash da senha nunca é serializado.
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
        """Valida a senha; hashes MD5 legados são aceitos uma vez e regravados com hash forte."""
        if LEGACY_MD5_PATTERN.match(self.password or ''):
            legacy = hashlib.md5(pwd.encode()).hexdigest()
            if not hmac.compare_digest(self.password, legacy):
                return False
            self.set_password(pwd)
            return True
        return check_password_hash(self.password, pwd)

    def is_admin(self):
        return self.role == ROLE_ADMIN
