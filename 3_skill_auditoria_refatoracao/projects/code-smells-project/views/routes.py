from flask import jsonify
import controllers

def register_routes(app):
    routes = [
        ('/produtos', 'listar_produtos', controllers.listar_produtos, ['GET']),
        ('/produtos/busca', 'buscar_produtos', controllers.buscar_produtos, ['GET']),
        ('/produtos/<int:id>', 'buscar_produto', controllers.buscar_produto, ['GET']),
        ('/produtos', 'criar_produto', controllers.criar_produto, ['POST']),
        ('/produtos/<int:id>', 'atualizar_produto', controllers.atualizar_produto, ['PUT']),
        ('/produtos/<int:id>', 'deletar_produto', controllers.deletar_produto, ['DELETE']),
        ('/usuarios', 'listar_usuarios', controllers.listar_usuarios, ['GET']),
        ('/usuarios/<int:id>', 'buscar_usuario', controllers.buscar_usuario, ['GET']),
        ('/usuarios', 'criar_usuario', controllers.criar_usuario, ['POST']),
        ('/login', 'login', controllers.login, ['POST']),
        ('/pedidos', 'criar_pedido', controllers.criar_pedido, ['POST']),
        ('/pedidos', 'listar_todos_pedidos', controllers.listar_todos_pedidos, ['GET']),
        ('/pedidos/usuario/<int:usuario_id>', 'listar_pedidos_usuario', controllers.listar_pedidos_usuario, ['GET']),
        ('/pedidos/<int:pedido_id>/status', 'atualizar_status_pedido', controllers.atualizar_status_pedido, ['PUT']),
        ('/relatorios/vendas', 'relatorio_vendas', controllers.relatorio_vendas, ['GET']),
        ('/health', 'health_check', controllers.health_check, ['GET']),
    ]
    for rule, endpoint, view, methods in routes:
        app.add_url_rule(rule, endpoint, view, methods=methods)
