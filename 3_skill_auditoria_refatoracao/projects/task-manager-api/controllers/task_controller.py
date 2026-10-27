import logging

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from controllers.errors import NotFoundError, ValidationError, commit
from controllers.validation import (
    normalize_tags,
    parse_due_date,
    parse_int,
    require_payload,
    validate_priority,
    validate_status,
    validate_title,
)
from database import db
from models.category import Category
from models.constants import DEFAULT_PRIORITY, DEFAULT_STATUS, DONE_STATUS, TASK_STATUSES
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, utc_now

logger = logging.getLogger(__name__)


def get_task_or_404(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def list_tasks():
    return (
        Task.query.options(joinedload(Task.user), joinedload(Task.category))
        .order_by(Task.id)
        .all()
    )


def _resolve_user_id(value):
    if not value:
        return None
    user_id = parse_int(value, 'Usuário não encontrado')
    if not db.session.get(User, user_id):
        raise NotFoundError('Usuário não encontrado')
    return user_id


def _resolve_category_id(value):
    if not value:
        return None
    category_id = parse_int(value, 'Categoria não encontrada')
    if not db.session.get(Category, category_id):
        raise NotFoundError('Categoria não encontrada')
    return category_id


def create_task(data):
    require_payload(data)

    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    validate_title(title)
    status = validate_status(data.get('status', DEFAULT_STATUS))
    priority = validate_priority(data.get('priority', DEFAULT_PRIORITY))
    user_id = _resolve_user_id(data.get('user_id'))
    category_id = _resolve_category_id(data.get('category_id'))

    task = Task(
        title=title,
        description=data.get('description', ''),
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
    )
    if data.get('due_date'):
        task.due_date = parse_due_date(data['due_date'])
    if data.get('tags'):
        task.tags = normalize_tags(data['tags'])

    db.session.add(task)
    commit('Erro ao criar task')
    logger.info('Task criada: id=%s', task.id)
    return task


def update_task(task_id, data):
    task = get_task_or_404(task_id)
    require_payload(data)

    # Valida tudo antes de alterar a entidade, na mesma ordem da versão anterior.
    changes = {}
    if 'title' in data:
        changes['title'] = validate_title(data['title'])
    if 'description' in data:
        changes['description'] = data['description']
    if 'status' in data:
        changes['status'] = validate_status(data['status'])
    if 'priority' in data:
        changes['priority'] = validate_priority(data['priority'])
    if 'user_id' in data:
        changes['user_id'] = _resolve_user_id(data['user_id'])
    if 'category_id' in data:
        changes['category_id'] = _resolve_category_id(data['category_id'])
    if 'due_date' in data:
        changes['due_date'] = parse_due_date(data['due_date']) if data['due_date'] else None
    if 'tags' in data:
        changes['tags'] = normalize_tags(data['tags']) if data['tags'] is not None else None

    for field, value in changes.items():
        setattr(task, field, value)
    task.updated_at = utc_now()

    commit('Erro ao atualizar')
    logger.info('Task atualizada: id=%s', task.id)
    return task


def delete_task(task_id):
    task = get_task_or_404(task_id)
    db.session.delete(task)
    commit('Erro ao deletar')
    logger.info('Task deletada: id=%s', task_id)


def search_tasks(text='', status='', priority='', user_id=''):
    query = Task.query
    if text:
        query = query.filter(db.or_(Task.title.like(f'%{text}%'), Task.description.like(f'%{text}%')))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == parse_int(priority, 'Prioridade inválida'))
    if user_id:
        query = query.filter(Task.user_id == parse_int(user_id, 'user_id inválido'))
    return query.order_by(Task.id).all()


def count_by_status():
    counts = dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
    return {status: counts.get(status, 0) for status in TASK_STATUSES}, sum(counts.values())


def task_stats():
    by_status, total = count_by_status()
    overdue = Task.query.filter(Task.overdue_filter()).count()
    return {
        'total': total,
        **by_status,
        'overdue': overdue,
        'completion_rate': calculate_percentage(by_status[DONE_STATUS], total),
    }
