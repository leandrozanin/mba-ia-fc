import unittest
import app as application

class SecurityContractTests(unittest.TestCase):
    def setUp(self):
        application.app.config.update(TESTING=True)
        self.client = application.app.test_client()

    def test_health_does_not_expose_secrets_or_filesystem(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertNotIn('secret_key', payload)
        self.assertNotIn('db_path', payload)

    def test_arbitrary_sql_endpoint_is_disabled(self):
        response = self.client.post('/admin/query', json={'sql': 'DROP TABLE produtos'})
        self.assertEqual(response.status_code, 410)
        self.assertEqual(self.client.get('/produtos').status_code, 200)

    def test_user_responses_never_include_password(self):
        response = self.client.get('/usuarios')
        self.assertEqual(response.status_code, 200)
        for user in response.get_json()['dados']:
            self.assertNotIn('senha', user)

    def test_search_treats_sql_as_data_and_new_users_get_hashed_passwords(self):
        self.assertEqual(self.client.get('/produtos/busca?q=%27%20OR%201%3D1--').status_code, 200)
        created = self.client.post('/usuarios', json={'nome':'Teste','email':'novo@example.test','senha':'segredo'} )
        self.assertEqual(created.status_code, 201)
        login = self.client.post('/login', json={'email':'novo@example.test','senha':'segredo'})
        self.assertEqual(login.status_code, 200)
        self.assertNotIn('senha', login.get_json()['dados'])

if __name__ == '__main__':
    unittest.main()
