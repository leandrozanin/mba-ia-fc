from flask import Blueprint, jsonify, request

from controllers import category_controller
from routes.auth import login_required
from routes.serializers import category_list_item

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = category_controller.list_categories_with_task_count()
    return jsonify([category_list_item(c, count) for c, count in categories]), 200


@category_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    category = category_controller.create_category(request.get_json())
    return jsonify(category.to_dict()), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@login_required
def update_category(cat_id):
    category = category_controller.update_category(cat_id, request.get_json())
    return jsonify(category.to_dict()), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@login_required
def delete_category(cat_id):
    category_controller.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
