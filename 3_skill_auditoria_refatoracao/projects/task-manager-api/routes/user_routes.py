from flask import Blueprint, current_app, g, jsonify, request

from controllers import auth_controller, user_controller
from routes.auth import admin_required, current_user_or_none, login_required
from routes.serializers import tasks, user_list_item, user_task_item

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    users = user_controller.list_users_with_task_count()
    return jsonify([user_list_item(u, count) for u, count in users]), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = user_controller.get_user_or_404(user_id)
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in user_controller.get_user_tasks(user_id)]
    return jsonify(data), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    user = user_controller.create_user(request.get_json(), current_user_or_none())
    return jsonify(user.to_dict()), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    user = user_controller.update_user(user_id, request.get_json(), g.current_user)
    return jsonify(user.to_dict()), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user_controller.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    return jsonify(tasks(user_controller.get_user_tasks(user_id), user_task_item)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    user, token = auth_controller.login(request.get_json(), current_app.extensions['auth_service'])
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
    }), 200
