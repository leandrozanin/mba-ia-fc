import os
import shutil
import tempfile
import unittest
from unittest import mock

from sqlalchemy import event

from app import create_app
from database import db
from seed import seed_data

TEST_SECRET = 'test-secret-key-not-for-production'


class ApiTestCase(unittest.TestCase):
    """App com SQLite temporário e os dados do seed.py."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(self._tmpdir, 'test.db').replace('\\', '/')
        with mock.patch('config.load_dotenv'):
            self.app = create_app({
                'SECRET_KEY': TEST_SECRET,
                'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_path,
                'TESTING': True,
            })
        seed_data(self.app)
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def token_for(self, email, password):
        resp = self.client.post('/login', json={'email': email, 'password': password})
        self.assertEqual(resp.status_code, 200, resp.get_json())
        return resp.get_json()['token']

    def auth(self, email='joao@email.com', password='1234'):
        return {'Authorization': 'Bearer ' + self.token_for(email, password)}

    def count_queries(self, func):
        with self.app.app_context():
            engine = db.engine
        statements = []

        def before_execute(conn, cursor, statement, *args):
            statements.append(statement)

        event.listen(engine, 'before_cursor_execute', before_execute)
        try:
            result = func()
        finally:
            event.remove(engine, 'before_cursor_execute', before_execute)
        return result, len(statements)
