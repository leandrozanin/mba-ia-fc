from models import pedido_model

# (faturamento mínimo exclusivo, taxa de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]


def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def relatorio_vendas():
    resumo = pedido_model.resumo_vendas()
    total_pedidos = resumo["total_pedidos"]
    faturamento = resumo["faturamento"]
    desconto = calcular_desconto(faturamento)
    por_status = resumo["por_status"]

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": por_status.get("pendente", 0),
        "pedidos_aprovados": por_status.get("aprovado", 0),
        "pedidos_cancelados": por_status.get("cancelado", 0),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
