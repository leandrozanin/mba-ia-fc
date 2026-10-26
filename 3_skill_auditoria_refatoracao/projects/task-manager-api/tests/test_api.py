import hashlib
import os
import sys
import tempfile
import unittest
import warnings
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from database import db  # noqa: E402
from models.category import Category  # noqa: E402
from models.task import Task  # noqa: E402
from models.user import User  # noqa: E402
from utils.dates import utcnow  # noqa: E402

PASSWORD = 'senha-segura'


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.app = create_app({
            'SECRET_KEY': 'test-secret',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(self.tmp.name, 'test.db'),
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            for name, email, role in (('Admin', 'admin@t.com', 'admin'), ('Ana', 'ana@t.com', 'user'), ('Bia', 'bia@t.com', 'user')):
                user = User(name=name, email=email, role=role)
                user.set_password(PASSWORD)
                db.session.add(user)
            db.session.add(Category(name='Backend', color='#123456'))
            db.session.flush()
            db.session.add_all([
                Task(title='Atrasada', status='pending', priority=1, user_id=2, category_id=1, due_date=utcnow() - timedelta(days=2)),
                Task(title='Concluída', status='done', priority=3, user_id=2, category_id=1, due_date=utcnow() - timedelta(days=2)),
                Task(title='Futura', status='pending', priority=2, user_id=3),
            ])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.engine.dispose()
        self.tmp.cleanup()

    def token(self, email='admin@t.com', password=PASSWORD):
        resposta = self.client.post('/login', json={'email': email, 'password': password})
        self.assertEqual(resposta.status_code, 200, resposta.get_json())
        return {'Authorization': 'Bearer ' + resposta.get_json()['token']}


class SegurancaTests(ApiTestCase):
    def test_respostas_nunca_incluem_hash_de_senha(self):
        respostas = [
            self.client.get('/users').get_json()[0],
            self.client.get('/users/1').get_json(),
            self.client.post('/users', json={'name': 'Novo', 'email': 'novo@t.com', 'password': PASSWORD}).get_json(),
            self.client.post('/login', json={'email': 'ana@t.com', 'password': PASSWORD}).get_json()['user'],
        ]
        for corpo in respostas:
            self.assertNotIn('password', corpo)

    def test_senha_usa_hash_com_salt(self):
        with self.app.app_context():
            senha = db.session.get(User, 1).password
        self.assertFalse(senha.startswith(hashlib.md5(PASSWORD.encode()).hexdigest()))
        self.assertIn('$', senha)

    def test_hash_md5_legado_e_migrado_no_login(self):
        with self.app.app_context():
            user = db.session.get(User, 2)
            user.password = hashlib.md5(PASSWORD.encode()).hexdigest()
            db.session.commit()
        self.assertEqual(self.client.post('/login', json={'email': 'ana@t.com', 'password': 'errada'}).status_code, 401)
        self.token('ana@t.com')
        with self.app.app_context():
            self.assertNotRegex(db.session.get(User, 2).password, r'^[0-9a-f]{32}$')

    def test_token_e_assinado_e_nao_previsivel(self):
        token = self.client.post('/login', json={'email': 'ana@t.com', 'password': PASSWORD}).get_json()['token']
        self.assertNotEqual(token, 'fake-jwt-token-2')
        falso = {'Authorization': 'Bearer fake-jwt-token-1'}
        self.assertEqual(self.client.delete('/users/3', headers=falso).status_code, 401)

    def test_escrita_de_usuarios_exige_autenticacao_e_papel(self):
        self.assertEqual(self.client.put('/users/2', json={'role': 'admin'}).status_code, 401)
        ana = self.token('ana@t.com')
        self.assertEqual(self.client.put('/users/2', json={'role': 'admin'}, headers=ana).status_code, 403)
        self.assertEqual(self.client.put('/users/3', json={'name': 'Outra'}, headers=ana).status_code, 403)
        self.assertEqual(self.client.put('/users/2', json={'name': 'Ana Maria'}, headers=ana).status_code, 200)
        self.assertEqual(self.client.delete('/users/3', headers=ana).status_code, 403)
        self.assertEqual(self.client.delete('/users/3', headers=self.token()).status_code, 200)

    def test_autocadastro_nao_cria_admin(self):
        corpo = {'name': 'Hacker', 'email': 'h@t.com', 'password': PASSWORD, 'role': 'admin'}
        self.assertEqual(self.client.post('/users', json=corpo).status_code, 403)
        self.assertEqual(self.client.post('/users', json=corpo, headers=self.token()).status_code, 201)

    def test_categorias_exigem_admin_ou_manager(self):
        self.assertEqual(self.client.post('/categories', json={'name': 'X'}).status_code, 401)
        self.assertEqual(self.client.post('/categories', json={'name': 'X'}, headers=self.token('ana@t.com')).status_code, 403)
        self.assertEqual(self.client.post('/categories', json={'name': 'X'}, headers=self.token()).status_code, 201)


class ValidacaoTests(ApiTestCase):
    def test_tipos_invalidos_retornam_400(self):
        self.assertEqual(self.client.post('/tasks', json={'title': 'Valida', 'priority': '2'}).status_code, 400)
        self.assertEqual(self.client.post('/tasks', json={'title': 123}).status_code, 400)
        self.assertEqual(self.client.put('/tasks/1', json={'priority': 'alta'}).status_code, 400)
        self.assertEqual(self.client.get('/tasks/search?priority=abc').status_code, 400)
        admin = self.token()
        self.assertEqual(self.client.put('/categories/1', headers=admin).status_code, 400)
        self.assertEqual(self.client.put('/categories/1', json={'color': 'azul'}, headers=admin).status_code, 400)
        self.assertEqual(self.client.put('/users/2', json={'active': 'sim'}, headers=admin).status_code, 400)
        self.assertEqual(self.client.put('/users/2', json={'name': ''}, headers=admin).status_code, 400)

    def test_update_de_task_usa_mesma_regra_do_create(self):
        self.assertEqual(self.client.put('/tasks/1', json={'title': ''}).status_code, 400)
        self.assertEqual(self.client.put('/tasks/1', json={'title': 'ab'}).status_code, 400)
        self.assertEqual(self.client.post('/tasks', json={'title': 'ab'}).status_code, 400)

    def test_referencias_inexistentes_retornam_404(self):
        self.assertEqual(self.client.post('/tasks', json={'title': 'Nova', 'user_id': 999}).status_code, 404)
        self.assertEqual(self.client.put('/tasks/1', json={'category_id': 999}).status_code, 404)


class RegrasTests(ApiTestCase):
    def test_overdue_consistente_entre_endpoints(self):
        self.assertTrue(self.client.get('/tasks/1').get_json()['overdue'])
        self.assertFalse(self.client.get('/tasks/2').get_json()['overdue'])
        listagem = {t['id']: t for t in self.client.get('/tasks').get_json()}
        self.assertTrue(listagem[1]['overdue'])
        self.assertEqual(listagem[1]['user_name'], 'Ana')
        self.assertEqual(listagem[1]['category_name'], 'Backend')
        self.assertEqual(self.client.get('/tasks/stats').get_json()['overdue'], 1)
        self.assertEqual(self.client.get('/reports/summary').get_json()['overdue']['count'], 1)
        self.assertEqual(self.client.get('/reports/user/2').get_json()['statistics']['overdue'], 1)

    def test_relatorio_resumo_agrega_por_usuario(self):
        corpo = self.client.get('/reports/summary').get_json()
        self.assertEqual(corpo['overview'], {'total_tasks': 3, 'total_users': 3, 'total_categories': 1})
        self.assertEqual(corpo['tasks_by_status'], {'pending': 2, 'in_progress': 0, 'done': 1, 'cancelled': 0})
        self.assertEqual(corpo['tasks_by_priority']['critical'], 1)
        ana = next(u for u in corpo['user_productivity'] if u['user_id'] == 2)
        self.assertEqual((ana['total_tasks'], ana['completed_tasks'], ana['completion_rate']), (2, 1, 50.0))

    def test_listagens_com_contagens(self):
        self.assertEqual({u['id']: u['task_count'] for u in self.client.get('/users').get_json()}, {1: 0, 2: 2, 3: 1})
        self.assertEqual(self.client.get('/categories').get_json()[0]['task_count'], 2)

    def test_excluir_categoria_desvincula_tasks(self):
        self.assertEqual(self.client.delete('/categories/1', headers=self.token()).status_code, 200)
        self.assertIsNone(self.client.get('/tasks/1').get_json()['category_id'])

    def test_excluir_usuario_remove_tasks_dele(self):
        self.assertEqual(self.client.delete('/users/2', headers=self.token()).status_code, 200)
        self.assertEqual(self.client.get('/tasks/1').status_code, 404)

    def test_sem_deprecation_warnings_de_utcnow_ou_query_get(self):
        with warnings.catch_warnings(record=True) as capturados:
            warnings.simplefilter('always')
            for rota in ('/tasks', '/tasks/1', '/users/2', '/users/2/tasks', '/reports/summary', '/reports/user/2'):
                self.client.get(rota)
            self.client.post('/tasks', json={'title': 'Warn', 'user_id': 2})
        mensagens = [str(w.message) for w in capturados]
        self.assertFalse([m for m in mensagens if 'utcnow' in m or 'Query.get' in m], mensagens)


if __name__ == '__main__':
    unittest.main()
