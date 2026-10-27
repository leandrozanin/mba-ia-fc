from tests.base import ApiTestCase


class UserTest(ApiTestCase):
    def test_list_with_task_count(self):
        users = self.client.get('/users').get_json()
        self.assertEqual([(u['id'], u['task_count']) for u in users], [(1, 4), (2, 3), (3, 3)])

    def test_list_query_count_is_constant(self):
        _, queries = self.count_queries(lambda: self.client.get('/users'))
        self.assertLessEqual(queries, 2)

    def test_get_user_with_tasks(self):
        body = self.client.get('/users/1').get_json()
        self.assertEqual(len(body['tasks']), 4)
        self.assertEqual(self.client.get('/users/999').status_code, 404)

    def test_user_tasks_format(self):
        tasks = self.client.get('/users/1/tasks').get_json()
        self.assertEqual(set(tasks[0]), {'id', 'title', 'description', 'status', 'priority',
                                         'created_at', 'due_date', 'overdue'})

    def test_create_validation(self):
        base = {'name': 'Ana', 'email': 'ana@email.com', 'password': 'senha-forte-1'}
        self.assertEqual(self.client.post('/users', json=base).status_code, 201)
        cases = [
            (base, 409, 'Email já cadastrado'),
            ({**base, 'name': ''}, 400, 'Nome é obrigatório'),
            ({**base, 'email': 'ana'}, 400, 'Email inválido'),
            ({**base, 'email': 'b@email.com', 'password': '1234567'}, 400, 'Senha deve ter no mínimo 8 caracteres'),
            ({**base, 'email': 'c@email.com', 'role': 'root'}, 400, 'Role inválido'),
        ]
        for body, status, message in cases:
            resp = self.client.post('/users', json=body)
            self.assertEqual((resp.status_code, resp.get_json()), (status, {'error': message}), body)

    def test_update_validation(self):
        headers = self.auth()
        cases = [
            ({'name': ''}, 400, 'Nome é obrigatório'),
            ({'email': 'pedro@email.com'}, 409, 'Email já cadastrado'),
            ({'password': '123'}, 400, 'Senha muito curta'),
            ({'active': 'sim'}, 400, 'Campo active deve ser booleano'),
            ({'role': 'root'}, 400, 'Role inválido'),
        ]
        for body, status, message in cases:
            resp = self.client.put('/users/2', json=body, headers=headers)
            self.assertEqual((resp.status_code, resp.get_json()), (status, {'error': message}), body)

    def test_update_password_then_login(self):
        resp = self.client.put('/users/2', json={'password': 'nova-senha-123'},
                               headers=self.auth('maria@email.com', 'abcd'))
        self.assertEqual(resp.status_code, 200)
        self.token_for('maria@email.com', 'nova-senha-123')

    def test_inactive_user_cannot_login(self):
        self.client.put('/users/2', json={'active': False}, headers=self.auth())
        resp = self.client.post('/login', json={'email': 'maria@email.com', 'password': 'abcd'})
        self.assertEqual((resp.status_code, resp.get_json()), (403, {'error': 'Usuário inativo'}))

    def test_login_missing_fields(self):
        resp = self.client.post('/login', json={'email': 'maria@email.com'})
        self.assertEqual((resp.status_code, resp.get_json()), (400, {'error': 'Email e senha são obrigatórios'}))


class ReportTest(ApiTestCase):
    def test_summary(self):
        report = self.client.get('/reports/summary').get_json()
        self.assertEqual(report['overview'], {'total_tasks': 10, 'total_users': 3, 'total_categories': 4})
        self.assertEqual(report['tasks_by_status'], {'pending': 6, 'in_progress': 2, 'done': 1, 'cancelled': 1})
        self.assertEqual(report['tasks_by_priority'], {'critical': 2, 'high': 3, 'medium': 3, 'low': 2, 'minimal': 0})
        self.assertEqual(report['overdue']['count'], 2)
        self.assertEqual([(t['id'], t['days_overdue']) for t in report['overdue']['tasks']], [(1, 3), (4, 1)])
        self.assertEqual(report['recent_activity'], {'tasks_created_last_7_days': 10, 'tasks_completed_last_7_days': 1})
        self.assertEqual(
            [(u['user_id'], u['total_tasks'], u['completed_tasks'], u['completion_rate']) for u in report['user_productivity']],
            [(1, 4, 0, 0.0), (2, 3, 0, 0.0), (3, 3, 1, 33.33)],
        )

    def test_summary_query_count_is_constant(self):
        _, queries = self.count_queries(lambda: self.client.get('/reports/summary'))
        self.assertLessEqual(queries, 9)

    def test_user_report(self):
        stats = self.client.get('/reports/user/1').get_json()['statistics']
        self.assertEqual(stats, {'total_tasks': 4, 'done': 0, 'pending': 4, 'in_progress': 0, 'cancelled': 0,
                                 'overdue': 2, 'high_priority': 2, 'completion_rate': 0.0})
        self.assertEqual(self.client.get('/reports/user/999').status_code, 404)


class CategoryTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.headers = self.auth()

    def test_list_with_task_count(self):
        categories = self.client.get('/categories').get_json()
        self.assertEqual([(c['name'], c['task_count']) for c in categories],
                         [('Backend', 6), ('Frontend', 1), ('DevOps', 2), ('Bug', 1)])

    def test_create_and_validation(self):
        resp = self.client.post('/categories', json={'name': 'QA'}, headers=self.headers)
        self.assertEqual((resp.status_code, resp.get_json()['color']), (201, '#000000'))
        cases = [
            ({'color': '#123456'}, 'Nome é obrigatório'),
            ({'name': 'QA', 'color': 'azul'}, 'Cor inválida. Use o formato #RRGGBB'),
        ]
        for body, message in cases:
            resp = self.client.post('/categories', json=body, headers=self.headers)
            self.assertEqual((resp.status_code, resp.get_json()), (400, {'error': message}), body)

    def test_update_null_body_is_400(self):
        resp = self.client.put('/categories/1', data='null', content_type='application/json', headers=self.headers)
        self.assertEqual((resp.status_code, resp.get_json()), (400, {'error': 'Dados inválidos'}))

    def test_update(self):
        resp = self.client.put('/categories/1', json={'description': 'Novo'}, headers=self.headers)
        self.assertEqual(resp.get_json()['description'], 'Novo')
        self.assertEqual(self.client.put('/categories/999', json={'name': 'x'}, headers=self.headers).status_code, 404)

    def test_delete_detaches_tasks(self):
        self.assertEqual(self.client.delete('/categories/4', headers=self.headers).status_code, 200)
        task = self.client.get('/tasks/4').get_json()
        self.assertIsNone(task['category_id'])
