import warnings
from datetime import timedelta
from unittest import mock

from sqlalchemy.exc import OperationalError

from database import db
from models.task import Task
from tests.base import ApiTestCase
from utils.helpers import utc_now


class TaskReadTest(ApiTestCase):
    def test_list_contains_names_and_overdue(self):
        tasks = self.client.get('/tasks').get_json()
        self.assertEqual(len(tasks), 10)
        first = tasks[0]
        self.assertEqual(first['user_name'], 'João Silva')
        self.assertEqual(first['category_name'], 'Backend')
        self.assertTrue(first['overdue'])
        self.assertEqual(sum(t['overdue'] for t in tasks), 2)

    def test_list_query_count_does_not_grow_with_tasks(self):
        _, before = self.count_queries(lambda: self.client.get('/tasks'))
        with self.app.app_context():
            for i in range(20):
                db.session.add(Task(title='Extra %d' % i, user_id=1 + i % 3, category_id=1 + i % 4))
            db.session.commit()
        resp, after = self.count_queries(lambda: self.client.get('/tasks'))
        self.assertEqual(len(resp.get_json()), 30)
        self.assertEqual(before, after)

    def test_get_task_and_404(self):
        self.assertIn('overdue', self.client.get('/tasks/1').get_json())
        resp = self.client.get('/tasks/999')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json(), {'error': 'Task não encontrada'})

    def test_search(self):
        found = self.client.get('/tasks/search?q=API').get_json()
        self.assertEqual({t['id'] for t in found}, {5, 7})
        filtered = self.client.get('/tasks/search?status=pending&priority=1').get_json()
        self.assertEqual({t['id'] for t in filtered}, {1, 4})

    def test_search_invalid_numbers_return_400(self):
        self.assertEqual(self.client.get('/tasks/search?priority=x').status_code, 400)
        self.assertEqual(self.client.get('/tasks/search?user_id=x').status_code, 400)

    def test_stats(self):
        self.assertEqual(self.client.get('/tasks/stats').get_json(), {
            'total': 10, 'pending': 6, 'in_progress': 2, 'done': 1, 'cancelled': 1,
            'overdue': 2, 'completion_rate': 10.0,
        })

    def test_no_deprecated_api_warnings(self):
        headers = self.auth()
        with warnings.catch_warnings():
            warnings.simplefilter('error', DeprecationWarning)
            for path in ('/tasks', '/tasks/1', '/tasks/stats', '/users', '/users/1', '/reports/summary',
                         '/reports/user/1', '/categories'):
                self.assertEqual(self.client.get(path).status_code, 200, path)
            self.assertEqual(self.client.put('/tasks/1', json={'status': 'done'}, headers=headers).status_code, 200)


class TaskWriteTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.headers = self.auth()

    def post(self, body):
        return self.client.post('/tasks', json=body, headers=self.headers)

    def test_create(self):
        resp = self.post({'title': 'Nova task', 'priority': 2, 'user_id': 2, 'category_id': 1,
                          'due_date': '2030-01-15', 'tags': ['a', 'b']})
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body['tags'], ['a', 'b'])
        self.assertEqual(body['due_date'], '2030-01-15 00:00:00')
        self.assertEqual(body['status'], 'pending')

    def test_create_validation_messages(self):
        cases = [
            ({'description': 'x'}, 400, 'Título é obrigatório'),
            ({'title': 'ab'}, 400, 'Título muito curto'),
            ({'title': 'x' * 201}, 400, 'Título muito longo'),
            ({'title': 12345}, 400, 'Título inválido'),
            ({'title': 'abc', 'status': 'x'}, 400, 'Status inválido'),
            ({'title': 'abc', 'priority': 9}, 400, 'Prioridade deve ser entre 1 e 5'),
            ({'title': 'abc', 'priority': 'a'}, 400, 'Prioridade inválida'),
            ({'title': 'abc', 'priority': True}, 400, 'Prioridade inválida'),
            ({'title': 'abc', 'due_date': '15/01/2030'}, 400, 'Formato de data inválido. Use YYYY-MM-DD'),
            ({'title': 'abc', 'tags': [1, 2]}, 400, 'Tags inválidas'),
            ({'title': 'abc', 'user_id': 999}, 404, 'Usuário não encontrado'),
            ({'title': 'abc', 'category_id': 999}, 404, 'Categoria não encontrada'),
        ]
        for body, status, message in cases:
            resp = self.post(body)
            self.assertEqual((resp.status_code, resp.get_json()), (status, {'error': message}), body)

    def test_null_or_empty_body(self):
        for raw in ('null', '{}', '[]'):
            resp = self.client.post('/tasks', data=raw, content_type='application/json', headers=self.headers)
            self.assertEqual(resp.get_json(), {'error': 'Dados inválidos'}, raw)

    def test_update_validates_before_changing(self):
        resp = self.client.put('/tasks/1', json={'title': 'Título novo', 'status': 'x'}, headers=self.headers)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.client.get('/tasks/1').get_json()['title'], 'Implementar autenticação JWT')

    def test_update(self):
        resp = self.client.put('/tasks/1', json={'status': 'done', 'tags': 'x,y', 'due_date': None},
                               headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual((body['status'], body['tags'], body['due_date']), ('done', ['x', 'y'], None))
        self.assertFalse(self.client.get('/tasks/1').get_json()['overdue'])

    def test_update_clears_tags_with_empty_list(self):
        resp = self.client.put('/tasks/3', json={'tags': []}, headers=self.headers)
        self.assertEqual(resp.get_json()['tags'], [])

    def test_delete(self):
        self.assertEqual(self.client.delete('/tasks/2', headers=self.headers).status_code, 200)
        self.assertEqual(self.client.delete('/tasks/2', headers=self.headers).status_code, 404)

    def test_persistence_failure_rolls_back_with_original_message(self):
        with mock.patch('controllers.errors.db.session.commit',
                        side_effect=OperationalError('INSERT', {}, Exception('disk full'))):
            resp = self.post({'title': 'Nova task'})
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.get_json(), {'error': 'Erro ao criar task'})
        self.assertEqual(len(self.client.get('/tasks').get_json()), 10)


class OverdueRuleTest(ApiTestCase):
    def test_model_rule_matches_sql_rule(self):
        now = utc_now()
        with self.app.app_context():
            db.session.add_all([
                Task(title='Fechada atrasada', status='done', due_date=now - timedelta(days=1)),
                Task(title='Cancelada atrasada', status='cancelled', due_date=now - timedelta(days=1)),
                Task(title='Futura', status='pending', due_date=now + timedelta(days=1)),
            ])
            db.session.commit()
            python_rule = {t.id for t in Task.query.all() if t.is_overdue(now)}
            sql_rule = {t.id for t in Task.query.filter(Task.overdue_filter(now)).all()}
        self.assertEqual(python_rule, sql_rule)
        self.assertEqual(python_rule, {1, 4})
