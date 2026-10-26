import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.app = create_app({
            "SECRET_KEY": "test-secret",
            "DATABASE_PATH": os.path.join(self.tmp.name, "test.db"),
            "SEED_USER_PASSWORD": "senha-demo",
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def criar_usuario(self, email="cliente@teste.com", senha="segredo"):
        return self.client.post("/usuarios", json={"nome": "Cliente", "email": email, "senha": senha})

    def estoque(self, produto_id):
        return self.client.get(f"/produtos/{produto_id}").get_json()["dados"]["estoque"]


class SegurancaTests(ApiTestCase):
    def test_health_nao_expoe_segredo_nem_caminho(self):
        corpo = self.client.get("/health").get_json()
        self.assertEqual(corpo["status"], "ok")
        for chave in ("secret_key", "db_path", "debug"):
            self.assertNotIn(chave, corpo)

    def test_usuarios_nao_retornam_senha(self):
        for usuario in self.client.get("/usuarios").get_json()["dados"]:
            self.assertNotIn("senha", usuario)
        self.assertNotIn("senha", self.client.get("/usuarios/1").get_json()["dados"])

    def test_senha_armazenada_com_hash_e_login_funciona(self):
        self.criar_usuario()
        resposta = self.client.post("/login", json={"email": "cliente@teste.com", "senha": "segredo"})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["dados"]["email"], "cliente@teste.com")

    def test_login_com_sql_injection_e_recusado(self):
        resposta = self.client.post("/login", json={"email": "' OR '1'='1' --", "senha": "x"})
        self.assertEqual(resposta.status_code, 401)

    def test_busca_com_aspas_nao_quebra_query(self):
        resposta = self.client.get("/produtos/busca?q=' OR 1=1 --")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["total"], 0)

    def test_produto_com_apostrofo_pode_ser_criado(self):
        resposta = self.client.post("/produtos", json={"nome": "Monitor 32''", "preco": 10, "estoque": 1})
        self.assertEqual(resposta.status_code, 201)

    def test_admin_query_removido_e_reset_desabilitado(self):
        self.assertEqual(self.client.post("/admin/query", json={"sql": "SELECT 1"}).status_code, 404)
        self.assertEqual(self.client.post("/admin/reset-db").status_code, 403)
        self.assertGreater(len(self.client.get("/produtos").get_json()["dados"]), 0)

    def test_erro_inesperado_nao_vaza_detalhes(self):
        @self.app.get("/boom")
        def boom():
            raise RuntimeError("detalhe interno sqlite")

        resposta = self.client.get("/boom")
        self.assertEqual(resposta.status_code, 500)
        self.assertNotIn("sqlite", resposta.get_json()["erro"])


class ValidacaoTests(ApiTestCase):
    def test_update_aplica_mesma_validacao_do_create(self):
        resposta = self.client.put("/produtos/1", json={"nome": "X", "preco": 1, "estoque": 1})
        self.assertEqual(resposta.status_code, 400)
        resposta = self.client.put("/produtos/1", json={"nome": "Valido", "preco": 1, "estoque": 1, "categoria": "nada"})
        self.assertEqual(resposta.status_code, 400)

    def test_tipos_invalidos_viram_400(self):
        self.assertEqual(self.client.post("/produtos", json={"nome": "Abc", "preco": "dez", "estoque": 1}).status_code, 400)
        self.assertEqual(self.client.get("/produtos/busca?preco_min=abc").status_code, 400)
        self.assertEqual(self.client.post("/login", data="nao-json").status_code, 400)
        self.assertEqual(self.client.put("/pedidos/1/status").status_code, 400)

    def test_email_duplicado_e_recusado(self):
        self.assertEqual(self.criar_usuario().status_code, 201)
        self.assertEqual(self.criar_usuario().status_code, 409)


class PedidoTests(ApiTestCase):
    def test_quantidade_negativa_e_recusada(self):
        antes = self.estoque(2)
        resposta = self.client.post("/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": -5}]})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.estoque(2), antes)

    def test_itens_repetidos_somam_para_validar_estoque(self):
        estoque = self.estoque(6)
        itens = [{"produto_id": 6, "quantidade": estoque}, {"produto_id": 6, "quantidade": 1}]
        resposta = self.client.post("/pedidos", json={"usuario_id": 2, "itens": itens})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.estoque(6), estoque)
        self.assertEqual(self.client.get("/pedidos").get_json()["dados"], [])

    def test_falha_no_meio_nao_deixa_pedido_parcial(self):
        itens = [{"produto_id": 1, "quantidade": 1}, {"produto_id": 999, "quantidade": 1}]
        resposta = self.client.post("/pedidos", json={"usuario_id": 2, "itens": itens})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.client.get("/pedidos").get_json()["dados"], [])

    def test_pedido_lista_itens_e_cancelamento_devolve_estoque(self):
        antes = self.estoque(2)
        resposta = self.client.post("/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 3}]})
        self.assertEqual(resposta.status_code, 201)
        pedido_id = resposta.get_json()["dados"]["pedido_id"]
        self.assertEqual(self.estoque(2), antes - 3)

        pedidos = self.client.get("/pedidos/usuario/2").get_json()["dados"]
        self.assertEqual(pedidos[0]["itens"][0]["produto_nome"], "Mouse Wireless")

        self.assertEqual(self.client.put(f"/pedidos/{pedido_id}/status", json={"status": "cancelado"}).status_code, 200)
        self.assertEqual(self.estoque(2), antes)
        self.assertEqual(self.client.put(f"/pedidos/{pedido_id}/status", json={"status": "aprovado"}).status_code, 409)

    def test_status_de_pedido_inexistente_retorna_404(self):
        self.assertEqual(self.client.put("/pedidos/999/status", json={"status": "aprovado"}).status_code, 404)

    def test_relatorio_aplica_faixa_de_desconto(self):
        self.client.post("/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 1}]})
        dados = self.client.get("/relatorios/vendas").get_json()["dados"]
        self.assertEqual(dados["total_pedidos"], 1)
        self.assertEqual(dados["desconto_aplicavel"], round(5999.99 * 0.05, 2))
        self.assertEqual(dados["pedidos_pendentes"], 1)


if __name__ == "__main__":
    unittest.main()
