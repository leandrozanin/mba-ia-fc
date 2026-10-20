import unittest
from app import create_app
from database import db
from models.user import User

class AppContractTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        self.client = self.app.test_client()

    def test_core_endpoints(self):
        for path in ('/', '/health', '/tasks', '/tasks/search', '/tasks/stats', '/users', '/reports/summary', '/categories'):
            with self.subTest(path=path):
                self.assertIn(self.client.get(path).status_code, (200, 404))

    def test_secret_not_embedded_and_user_password_not_serialized(self):
        with open('app.py', encoding='utf-8-sig') as source:
            self.assertNotIn('super-secret-key-123', source.read())
        with self.app.app_context():
            user = User(name='Example', email='example@test.local')
            user.set_password('Strong!123')
            self.assertTrue(user.check_password('Strong!123'))
            self.assertFalse(user.check_password('wrong'))
            self.assertNotIn('password', user.to_dict())
            self.assertNotEqual(user.password, 'Strong!123')

if __name__ == '__main__':
    unittest.main()
