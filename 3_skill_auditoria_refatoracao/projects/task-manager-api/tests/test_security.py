import hashlib
import os
from unittest import mock

from werkzeug.security import check_password_hash

from config import ConfigError, load_config
from database import db
from models.user import User
from services.auth_service import AuthService
from tests.base import ApiTestCase, TEST_SECRET


class ConfigTest(ApiTestCase):
    def test_missing_secret_key_fails_fast(self):
        with mock.patch('config.load_dotenv'), mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigError):
                load_config()

    def test_debug_off_and_localhost_by_default(self):
        with mock.patch('config.load_dotenv'), mock.patch.dict(os.environ, {'SECRET_KEY': 'x'}, clear=True):
            config = load_config()
        self.assertFalse(config['RUN_DEBUG'])
        self.assertEqual(config['RUN_HOST'], '127.0.0.1')
        self.assertEqual(config['CORS_ORIGINS'], [])

    def test_cors_disabled_without_configured_origins(self):
        resp = self.client.get('/tasks', headers={'Origin': 'https://evil.example'})
        self.assertNotIn('Access-Control-Allow-Origin', resp.headers)


class PasswordExposureTest(ApiTestCase):
    def test_password_never_serialized(self):
        responses = [
            self.client.get('/users'),
            self.client.get('/users/1'),
            self.client.post('/login', json={'email': 'maria@email.com', 'password': 'abcd'}),
            self.client.post('/users', json={'name': 'Ana', 'email': 'ana@email.com', 'password': 'senha-forte-1'}),
        ]
        for resp in responses:
            self.assertNotIn('password', resp.get_data(as_text=True))

    def test_password_stored_with_salted_hash(self):
        self.client.post('/users', json={'name': 'Ana', 'email': 'ana@email.com', 'password': 'senha-forte-1'})
        with self.app.app_context():
            user = User.query.filter_by(email='ana@email.com').one()
            self.assertNotEqual(user.password, hashlib.md5(b'senha-forte-1').hexdigest())
            self.assertTrue(check_password_hash(user.password, 'senha-forte-1'))

    def test_legacy_md5_hash_still_logs_in_and_is_migrated(self):
        with self.app.app_context():
            user = db.session.get(User, 2)
            user.password = hashlib.md5(b'abcd').hexdigest()
            db.session.commit()

        resp = self.client.post('/login', json={'email': 'maria@email.com', 'password': 'abcd'})
        self.assertEqual(resp.status_code, 200)
        with self.app.app_context():
            user = db.session.get(User, 2)
            self.assertFalse(user.has_legacy_password())
            self.assertTrue(user.check_password('abcd'))

    def test_wrong_password_rejected(self):
        resp = self.client.post('/login', json={'email': 'maria@email.com', 'password': 'errada'})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json(), {'error': 'Credenciais inválidas'})


class AuthenticationTest(ApiTestCase):
    WRITE_REQUESTS = [
        ('POST', '/tasks', {'title': 'Nova task'}),
        ('PUT', '/tasks/1', {'status': 'done'}),
        ('DELETE', '/tasks/1', None),
        ('PUT', '/users/2', {'name': 'x'}),
        ('DELETE', '/users/2', None),
        ('POST', '/categories', {'name': 'QA'}),
        ('PUT', '/categories/1', {'name': 'x'}),
        ('DELETE', '/categories/1', None),
    ]

    def test_writes_require_token(self):
        for method, path, body in self.WRITE_REQUESTS:
            resp = self.client.open(path, method=method, json=body)
            self.assertEqual(resp.status_code, 401, (method, path))
            self.assertEqual(resp.get_json(), {'error': 'Autenticação necessária'})

    def test_old_fake_token_is_rejected(self):
        resp = self.client.post('/tasks', json={'title': 'Nova task'},
                                headers={'Authorization': 'Bearer fake-jwt-token-1'})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json(), {'error': 'Token inválido ou expirado'})

    def test_token_signed_with_other_key_is_rejected(self):
        with self.app.app_context():
            user = db.session.get(User, 1)
            forged = AuthService('outra-chave', 3600).issue_token(user)
        resp = self.client.delete('/tasks/1', headers={'Authorization': 'Bearer ' + forged})
        self.assertEqual(resp.status_code, 401)

    def test_expired_token_is_rejected(self):
        service = AuthService(TEST_SECRET, max_age=-1)
        self.assertIsNone(service.user_id_from_token(service.issue_token(User(id=1))))

    def test_inactive_user_token_is_rejected(self):
        headers = self.auth('maria@email.com', 'abcd')
        admin = self.auth()
        self.client.put('/users/2', json={'active': False}, headers=admin)
        resp = self.client.post('/tasks', json={'title': 'Nova task'}, headers=headers)
        self.assertEqual(resp.status_code, 401)

    def test_valid_token_allows_write(self):
        resp = self.client.post('/tasks', json={'title': 'Nova task'}, headers=self.auth('maria@email.com', 'abcd'))
        self.assertEqual(resp.status_code, 201)


class AuthorizationTest(ApiTestCase):
    def test_anonymous_cannot_create_admin(self):
        resp = self.client.post('/users', json={'name': 'X', 'email': 'x@email.com',
                                                'password': 'senha-forte-1', 'role': 'admin'})
        self.assertEqual(resp.status_code, 403)

    def test_regular_user_cannot_create_admin(self):
        resp = self.client.post('/users', json={'name': 'X', 'email': 'x@email.com',
                                                'password': 'senha-forte-1', 'role': 'admin'},
                                headers=self.auth('maria@email.com', 'abcd'))
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_create_admin(self):
        resp = self.client.post('/users', json={'name': 'X', 'email': 'x@email.com',
                                                'password': 'senha-forte-1', 'role': 'admin'},
                                headers=self.auth())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()['role'], 'admin')

    def test_anonymous_signup_as_user_still_works(self):
        resp = self.client.post('/users', json={'name': 'X', 'email': 'x@email.com', 'password': 'senha-forte-1'})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()['role'], 'user')

    def test_user_can_update_self_but_not_others(self):
        headers = self.auth('maria@email.com', 'abcd')
        self.assertEqual(self.client.put('/users/2', json={'name': 'Maria S.'}, headers=headers).status_code, 200)
        self.assertEqual(self.client.put('/users/3', json={'name': 'x'}, headers=headers).status_code, 403)

    def test_user_cannot_escalate_own_role(self):
        resp = self.client.put('/users/2', json={'role': 'admin'}, headers=self.auth('maria@email.com', 'abcd'))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(self.client.get('/users/2').get_json()['role'], 'user')

    def test_only_admin_deletes_users(self):
        self.assertEqual(self.client.delete('/users/3', headers=self.auth('maria@email.com', 'abcd')).status_code, 403)
        resp = self.client.delete('/users/3', headers=self.auth())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.client.get('/users/3').status_code, 404)
        self.assertEqual(self.client.get('/tasks/search?user_id=3').get_json(), [])
