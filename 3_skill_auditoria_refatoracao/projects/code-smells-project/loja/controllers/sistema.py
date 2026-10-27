from ..db import transacao
from ..models import pedido as pedido_model
from ..models import produto as produto_model
from ..models import usuario as usuario_model


def contagens(db):
    return {
        "produtos": produto_model.contar(db),
        "usuarios": usuario_model.contar(db),
        "pedidos": pedido_model.contar(db),
    }


def resetar_banco(db):
    with transacao(db):
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
            db.execute("DELETE FROM " + tabela)
