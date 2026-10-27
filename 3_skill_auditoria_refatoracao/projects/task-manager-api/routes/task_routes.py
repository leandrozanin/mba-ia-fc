from flask import Blueprint, jsonify, request

from controllers import task_controller
from routes.auth import login_required
from routes.serializers import task_detail, task_list_item, tasks

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(tasks(task_controller.list_tasks(), task_list_item)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(task_detail(task_controller.get_task_or_404(task_id))), 200


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    task = task_controller.create_task(request.get_json())
    return jsonify(task.to_dict()), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = task_controller.update_task(task_id, request.get_json())
    return jsonify(task.to_dict()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task_controller.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    results = task_controller.search_tasks(
        text=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )
    return jsonify([t.to_dict() for t in results]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.task_stats()), 200
