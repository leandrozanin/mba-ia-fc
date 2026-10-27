from flask import Blueprint, jsonify

from ..auth import admin_obrigatorio
from ..controllers import relatorios
from ..db import get_db

bp = Blueprint("relatorios", __name__)


@bp.get("/relatorios/vendas")
@admin_obrigatorio
def relatorio_vendas():
    return jsonify({"dados": relatorios.vendas(get_db()), "sucesso": True}), 200
