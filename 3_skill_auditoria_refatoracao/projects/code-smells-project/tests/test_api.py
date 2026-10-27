import logging
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from loja import create_app
from loja.controllers.relatorios import calcular_desconto
from loja.db import connect

# os testes simulam falhas de propósito; não poluir a saída com os tracebacks registrados
logging.disable(logging.CRITICAL)

ADMIN_EMAIL = "admin@teste.local"
ADMIN_SENHA = "senha-admin-de-teste"


class NotificadorFake:
    def __init__(self):
        self.eventos = []

    def pedido_criado(self, pedido_id, usuario_id):
        self.eventos.append(("criado", pedido_id))

    def pedido_aprovado(self, pedido_id):
        self.eventos.append(("aprovado", pedido_id))

    def pedido_cancelado(self, pedido_id):
        self.eventos.append(("cancelado", pedido_id))


class ApiTestCase(unittest.TestCase):
    overrides = {}

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "teste.db")
        self.notificador = NotificadorFake()
        config = {
            "SECRET_KEY": "chave-de-teste",
            "DATABASE": self.db_path,
            "TESTING": True,
            "ADMIN_EMAIL": ADMIN_EMAIL,
            "ADMIN_PASSWORD": ADMIN_SENHA,
            "NOTIFICADOR": self.notificador,
        }
        config.update(self.overrides)
        self.app = create_app(config)
        self.client = self.app.test_client()
        self.admin = self.login(ADMIN_EMAIL, ADMIN_SENHA)

    def tearDown(self):
        self.tmpdir.cleanup()

    def query(self, sql, params=()):
        conexao = connect(self.db_path)
        try:
            return conexao.execute(sql, params).fetchall()
        finally:
            conexao.close()

    def login(self, email, senha):
        resp = self.client.post("/login", json={"email": email, "senha": senha})
        self.assertEqual(resp.status_code, 200, resp.get_json())
        return resp.get_json()["token"]

    def auth(self, token):
        return {"Authorization": "Bearer " + token}

    def criar_cliente(self, email="cliente@teste.local", senha="senha-cliente"):
        resp = self.client.post("/usuarios", json={"nome": "Cliente", "email": email, "senha": senha})
        self.assertEqual(resp.status_code, 201, resp.get_json())
        return resp.get_json()["dados"]["id"], self.login(email, senha)

    def estoque(self, produto_id):
        return self.client.get("/produtos/%d" % produto_id).get_json()["dados"]["estoque"]


class ConfigTest(unittest.TestCase):
    def test_sem_secret_key_nao_inicia(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                create_app({"DATABASE": ":memory:"})

    def test_debug_desligado_e_host_local_por_padrao(self):
        with mock.patch.dict(os.environ, {"SECRET_KEY": "x"}, clear=True):
            with tempfile.TemporaryDirectory() as tmp:
                app = create_app({"DATABASE": os.path.join(tmp, "t.db")})
        self.assertFalse(app.config["DEBUG"])
        self.assertEqual(app.config["HOST"], "127.0.0.1")
        self.assertEqual(app.config["CORS_ORIGINS"], [])


class SistemaTest(ApiTestCase):
    def test_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["versao"], "1.0.0")

    def test_health_nao_expoe_configuracao(self):
        resp = self.client.get("/health")
        corpo = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(corpo["counts"], {"produtos": 10, "usuarios": 1, "pedidos": 0})
        for chave in ("secret_key", "db_path", "debug", "ambiente"):
            self.assertNotIn(chave, corpo)

    def test_admin_query_removido(self):
        resp = self.client.post("/admin/query", json={"sql": "SELECT 1"}, headers=self.auth(self.admin))
        self.assertEqual(resp.status_code, 404)

    def test_reset_desabilitado_por_padrao(self):
        resp = self.client.post("/admin/reset-db", headers=self.auth(self.admin))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(self.query("SELECT COUNT(*) FROM produtos")[0][0], 10)

    def test_erro_inesperado_devolve_mensagem_generica(self):
        with mock.patch("loja.models.produto.listar", side_effect=RuntimeError("detalhe interno")):
            resp = self.client.get("/produtos")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.get_json()["erro"], "Erro interno do servidor")


class ResetHabilitadoTest(ApiTestCase):
    overrides = {"ENABLE_ADMIN_RESET": True}

    def test_reset_exige_admin(self):
        self.assertEqual(self.client.post("/admin/reset-db").status_code, 401)
        _, cliente = self.criar_cliente()
        self.assertEqual(self.client.post("/admin/reset-db", headers=self.auth(cliente)).status_code, 403)
        resp = self.client.post("/admin/reset-db", headers=self.auth(self.admin))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.query("SELECT COUNT(*) FROM produtos")[0][0], 0)


class ProdutosTest(ApiTestCase):
    produto = {"nome": "Livro D'Ávila", "descricao": "desc", "preco": 10.5, "estoque": 5, "categoria": "livros"}

    def test_listar_e_buscar(self):
        self.assertEqual(len(self.client.get("/produtos").get_json()["dados"]), 10)
        self.assertEqual(self.client.get("/produtos/1").get_json()["dados"]["nome"], "Notebook Gamer")
        self.assertEqual(self.client.get("/produtos/9999").status_code, 404)

    def test_escrita_exige_admin(self):
        self.assertEqual(self.client.post("/produtos", json=self.produto).status_code, 401)
        _, cliente = self.criar_cliente()
        self.assertEqual(self.client.post("/produtos", json=self.produto, headers=self.auth(cliente)).status_code, 403)
        self.assertEqual(self.client.delete("/produtos/1", headers=self.auth(cliente)).status_code, 403)

    def test_crud_com_apostrofo(self):
        h = self.auth(self.admin)
        resp = self.client.post("/produtos", json=self.produto, headers=h)
        self.assertEqual(resp.status_code, 201)
        produto_id = resp.get_json()["dados"]["id"]
        self.assertEqual(self.client.get("/produtos/%d" % produto_id).get_json()["dados"]["nome"], "Livro D'Ávila")

        resp = self.client.put("/produtos/%d" % produto_id, json=dict(self.produto, preco=12), headers=h)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.client.get("/produtos/%d" % produto_id).get_json()["dados"]["preco"], 12)

        self.assertEqual(self.client.delete("/produtos/%d" % produto_id, headers=h).status_code, 200)
        self.assertEqual(self.client.delete("/produtos/%d" % produto_id, headers=h).status_code, 404)

    def test_validacao_create_e_update_coerentes(self):
        h = self.auth(self.admin)
        invalidos = [
            ({"preco": 1, "estoque": 1}, "Nome é obrigatório"),
            (dict(self.produto, preco=-1), "Preço não pode ser negativo"),
            (dict(self.produto, preco="abc"), "Preço deve ser numérico"),
            (dict(self.produto, estoque=1.5), "Estoque deve ser um número inteiro"),
            (dict(self.produto, nome="A"), "Nome muito curto"),
            (dict(self.produto, categoria="xyz"), None),
        ]
        for corpo, mensagem in invalidos:
            for metodo, url in (("post", "/produtos"), ("put", "/produtos/1")):
                resp = getattr(self.client, metodo)(url, json=corpo, headers=h)
                self.assertEqual(resp.status_code, 400, (metodo, corpo))
                if mensagem:
                    self.assertEqual(resp.get_json()["erro"], mensagem)
        self.assertEqual(self.client.put("/produtos/9999", json=self.produto, headers=h).status_code, 404)

    def test_busca(self):
        def total(qs):
            return self.client.get("/produtos/busca" + qs).get_json()["total"]
        self.assertEqual(total("?q=Mouse"), 1)
        self.assertEqual(total("?categoria=moveis"), 1)
        self.assertEqual(total("?preco_min=100&preco_max=300"), 3)
        self.assertEqual(total("?q=' OR 1=1 --"), 0)
        self.assertEqual(self.client.get("/produtos/busca?preco_min=abc").status_code, 400)


class UsuariosTest(ApiTestCase):
    def test_senha_guardada_com_hash_e_nunca_exposta(self):
        usuario_id, cliente = self.criar_cliente(senha="minha-senha")
        senha_salva = self.query("SELECT senha FROM usuarios WHERE id = ?", (usuario_id,))[0][0]
        self.assertNotEqual(senha_salva, "minha-senha")
        self.assertTrue(senha_salva.startswith(("scrypt:", "pbkdf2:")))

        lista = self.client.get("/usuarios", headers=self.auth(self.admin)).get_json()["dados"]
        self.assertTrue(lista)
        self.assertTrue(all("senha" not in u for u in lista))
        proprio = self.client.get("/usuarios/%d" % usuario_id, headers=self.auth(cliente)).get_json()["dados"]
        self.assertNotIn("senha", proprio)

    def test_autorizacao_de_leitura(self):
        _, cliente = self.criar_cliente()
        self.assertEqual(self.client.get("/usuarios").status_code, 401)
        self.assertEqual(self.client.get("/usuarios", headers=self.auth(cliente)).status_code, 403)
        self.assertEqual(self.client.get("/usuarios/1", headers=self.auth(cliente)).status_code, 403)
        self.assertEqual(self.client.get("/usuarios/9999", headers=self.auth(self.admin)).status_code, 404)
        self.assertEqual(self.client.get("/usuarios", headers={"Authorization": "Bearer lixo"}).status_code, 401)

    def test_cadastro_validacoes(self):
        self.criar_cliente(email="dup@teste.local")
        resp = self.client.post("/usuarios", json={"nome": "X", "email": "dup@teste.local", "senha": "s"})
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(self.client.post("/usuarios", json={"nome": "X"}).status_code, 400)
        resp = self.client.post("/usuarios", json={"nome": "X", "email": "sem-arroba", "senha": "s"})
        self.assertEqual(resp.status_code, 400)

    def test_login(self):
        self.criar_cliente(email="c@teste.local", senha="certa")
        resp = self.client.post("/login", json={"email": "c@teste.local", "senha": "certa"})
        corpo = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(set(corpo["dados"]), {"id", "nome", "email", "tipo"})
        self.assertIn("token", corpo)
        self.assertEqual(self.client.post("/login", json={"email": "c@teste.local", "senha": "errada"}).status_code, 401)
        self.assertEqual(self.client.post("/login", json={}).status_code, 400)
        self.assertEqual(self.client.post("/login", data="x", content_type="text/plain").status_code, 400)

    def test_login_resiste_a_sql_injection(self):
        resp = self.client.post("/login", json={"email": "' OR '1'='1' --", "senha": "x"})
        self.assertEqual(resp.status_code, 401)


class MigracaoSenhasTest(unittest.TestCase):
    def test_senhas_em_texto_puro_sao_migradas(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "legado.db")
            conexao = sqlite3.connect(caminho)
            conexao.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT,"
                            " senha TEXT, tipo TEXT DEFAULT 'cliente', criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            conexao.execute("INSERT INTO usuarios (nome, email, senha) VALUES ('Legado', 'legado@teste.local', 'antiga')")
            conexao.commit()
            conexao.close()

            app = create_app({"SECRET_KEY": "x", "DATABASE": caminho})
            client = app.test_client()
            resp = client.post("/login", json={"email": "legado@teste.local", "senha": "antiga"})
            self.assertEqual(resp.status_code, 200)
            conexao = sqlite3.connect(caminho)
            senha = conexao.execute("SELECT senha FROM usuarios").fetchone()[0]
            conexao.close()
            self.assertNotEqual(senha, "antiga")


class PedidosTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.usuario_id, self.cliente = self.criar_cliente()

    def criar_pedido(self, itens, usuario_id=None, token=None):
        corpo = {"usuario_id": usuario_id or self.usuario_id, "itens": itens}
        return self.client.post("/pedidos", json=corpo, headers=self.auth(token or self.cliente))

    def test_criar_pedido_baixa_estoque_e_notifica(self):
        resp = self.criar_pedido([{"produto_id": 2, "quantidade": 2}])
        self.assertEqual(resp.status_code, 201)
        dados = resp.get_json()["dados"]
        self.assertAlmostEqual(dados["total"], 179.8)
        self.assertEqual(self.estoque(2), 48)
        self.assertEqual(self.notificador.eventos, [("criado", dados["pedido_id"])])

    def test_criar_pedido_exige_autenticacao_e_dono(self):
        resp = self.client.post("/pedidos", json={"usuario_id": self.usuario_id, "itens": [{"produto_id": 2, "quantidade": 1}]})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(self.criar_pedido([{"produto_id": 2, "quantidade": 1}], usuario_id=1).status_code, 403)
        resp = self.criar_pedido([{"produto_id": 2, "quantidade": 1}], usuario_id=9999, token=self.admin)
        self.assertEqual(resp.status_code, 400)

    def test_itens_invalidos(self):
        for itens in ([], [{"produto_id": 2, "quantidade": -5}], [{"produto_id": 2}], [{"produto_id": "2", "quantidade": 1}], ["x"]):
            self.assertEqual(self.criar_pedido(itens).status_code, 400, itens)
        self.assertEqual(self.estoque(2), 50)
        resp = self.criar_pedido([{"produto_id": 9999, "quantidade": 1}])
        self.assertEqual(resp.get_json()["erro"], "Produto 9999 não encontrado")

    def test_estoque_insuficiente_nao_deixa_escrita_parcial(self):
        resp = self.criar_pedido([{"produto_id": 2, "quantidade": 1}, {"produto_id": 6, "quantidade": 999}])
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["erro"], "Estoque insuficiente para Cadeira Gamer")
        self.assertEqual(self.estoque(2), 50)
        self.assertEqual(self.query("SELECT COUNT(*) FROM pedidos")[0][0], 0)

    def test_item_repetido_respeita_estoque_total(self):
        resp = self.criar_pedido([{"produto_id": 6, "quantidade": 5}, {"produto_id": 6, "quantidade": 5}])
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.estoque(6), 8)

    def test_falha_intermediaria_faz_rollback(self):
        with mock.patch("loja.models.pedido.adicionar_item", side_effect=sqlite3.OperationalError("falha simulada")):
            resp = self.criar_pedido([{"produto_id": 2, "quantidade": 3}])
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(self.estoque(2), 50)
        self.assertEqual(self.query("SELECT COUNT(*) FROM pedidos")[0][0], 0)
        self.assertEqual(self.criar_pedido([{"produto_id": 2, "quantidade": 1}]).status_code, 201)

    def test_listagens_com_itens(self):
        pedido_id = self.criar_pedido([{"produto_id": 2, "quantidade": 1}, {"produto_id": 3, "quantidade": 2}]).get_json()["dados"]["pedido_id"]
        self.client.delete("/produtos/3", headers=self.auth(self.admin))

        proprios = self.client.get("/pedidos/usuario/%d" % self.usuario_id, headers=self.auth(self.cliente)).get_json()["dados"]
        self.assertEqual(len(proprios), 1)
        self.assertEqual(proprios[0]["id"], pedido_id)
        self.assertEqual([(i["produto_nome"], i["quantidade"]) for i in proprios[0]["itens"]],
                         [("Mouse Wireless", 1), ("Desconhecido", 2)])

        todos = self.client.get("/pedidos", headers=self.auth(self.admin)).get_json()["dados"]
        self.assertEqual(todos, proprios)
        self.assertEqual(self.client.get("/pedidos", headers=self.auth(self.cliente)).status_code, 403)
        self.assertEqual(self.client.get("/pedidos/usuario/1", headers=self.auth(self.cliente)).status_code, 403)

    def test_status(self):
        pedido_id = self.criar_pedido([{"produto_id": 2, "quantidade": 4}]).get_json()["dados"]["pedido_id"]
        url = "/pedidos/%d/status" % pedido_id
        h = self.auth(self.admin)
        self.assertEqual(self.client.put(url, json={"status": "aprovado"}, headers=self.auth(self.cliente)).status_code, 403)
        self.assertEqual(self.client.put(url, json={"status": "xyz"}, headers=h).status_code, 400)
        self.assertEqual(self.client.put("/pedidos/9999/status", json={"status": "aprovado"}, headers=h).status_code, 404)

        self.assertEqual(self.client.put(url, json={"status": "aprovado"}, headers=h).status_code, 200)
        self.assertEqual(self.estoque(2), 46)
        self.assertEqual(self.client.put(url, json={"status": "cancelado"}, headers=h).status_code, 200)
        self.assertEqual(self.estoque(2), 50)
        self.assertEqual(self.client.put(url, json={"status": "cancelado"}, headers=h).status_code, 200)
        self.assertEqual(self.estoque(2), 50)
        self.assertEqual(self.client.put(url, json={"status": "aprovado"}, headers=h).status_code, 400)
        self.assertEqual([e for e, _ in self.notificador.eventos], ["criado", "aprovado", "cancelado"])


class RelatorioTest(ApiTestCase):
    def test_relatorio(self):
        usuario_id, cliente = self.criar_cliente()
        self.client.post("/pedidos", json={"usuario_id": usuario_id, "itens": [{"produto_id": 1, "quantidade": 1}]},
                         headers=self.auth(cliente))
        self.assertEqual(self.client.get("/relatorios/vendas", headers=self.auth(cliente)).status_code, 403)
        dados = self.client.get("/relatorios/vendas", headers=self.auth(self.admin)).get_json()["dados"]
        self.assertEqual(dados, {
            "total_pedidos": 1,
            "faturamento_bruto": 5999.99,
            "desconto_aplicavel": 300.0,
            "faturamento_liquido": 5699.99,
            "pedidos_pendentes": 1,
            "pedidos_aprovados": 0,
            "pedidos_cancelados": 0,
            "ticket_medio": 5999.99,
        })

    def test_relatorio_vazio(self):
        dados = self.client.get("/relatorios/vendas", headers=self.auth(self.admin)).get_json()["dados"]
        self.assertEqual(dados["total_pedidos"], 0)
        self.assertEqual(dados["faturamento_bruto"], 0)
        self.assertEqual(dados["ticket_medio"], 0)


class DescontoTest(unittest.TestCase):
    def test_faixas(self):
        self.assertEqual(calcular_desconto(1000), 0)
        self.assertAlmostEqual(calcular_desconto(1001), 20.02)
        self.assertAlmostEqual(calcular_desconto(5001), 250.05)
        self.assertAlmostEqual(calcular_desconto(10001), 1000.1)


if __name__ == "__main__":
    unittest.main()
