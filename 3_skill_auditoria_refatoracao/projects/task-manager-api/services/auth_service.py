from itsdangerous import BadSignature, URLSafeTimedSerializer


class AuthService:
    """Emite e verifica tokens assinados com SECRET_KEY e prazo de validade."""

    _SALT = 'task-manager-auth'

    def __init__(self, secret_key, max_age):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=self._SALT)
        self._max_age = max_age

    def issue_token(self, user):
        return self._serializer.dumps({'uid': user.id})

    def user_id_from_token(self, token):
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except BadSignature:  # inclui SignatureExpired
            return None
        user_id = payload.get('uid') if isinstance(payload, dict) else None
        return user_id if isinstance(user_id, int) else None
