import logging

from flask import current_app
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from controllers.validators import parse_int_arg, validate_task
from database import db
from errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import CLOSED_STATUSES, STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING
from utils.dates import utcnow

logger = logging.getLogger(__name__)


def get_task_or_404(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_references(fields):
    if fields.get('user_id') and db.session.get(User, fields['user_id']) is None:
        raise NotFoundError('Usuário não encontrado')
    if fields.get('category_id') and db.session.get(Category, fields['category_id']) is None:
        raise NotFoundError('Categoria não encontrada')


def overdue_filter(now=None):
    return db.and_(Task.due_date.is_not(None), Task.due_date < (now or utcnow()), Task.status.not_in(CLOSED_STATUSES))


def list_tasks():
    # joinedload traz usuário e categoria na mesma consulta (antes: 1 + 2N).
    query = db.select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
    return [task.to_list_dict() for task in db.session.scalars(query)]


def get_task(task_id):
    return get_task_or_404(task_id).to_detail_dict()


def create_task(data):
    fields = validate_task(data)
    _ensure_references(fields)

    task = Task(**fields)
    db.session.add(task)
    db.session.commit()
    logger.info('Task criada: id=%s', task.id)

    if task.user:
        current_app.extensions['notifier'].notify_task_assigned(task.user, task)
    return task.to_dict()


def update_task(task_id, data):
    task = get_task_or_404(task_id)
    fields = validate_task(data, partial=True)
    _ensure_references(fields)

    for field, value in fields.items():
        setattr(task, field, value)
    task.updated_at = utcnow()
    db.session.commit()
    logger.info('Task atualizada: id=%s', task.id)
    return task.to_dict()


def delete_task(task_id):
    db.session.delete(get_task_or_404(task_id))
    db.session.commit()
    logger.info('Task deletada: id=%s', task_id)


def search_tasks(args):
    query = db.select(Task)
    term = args.get('q', '')
    if term:
        query = query.where(db.or_(Task.title.like(f'%{term}%'), Task.description.like(f'%{term}%')))
    if args.get('status'):
        query = query.where(Task.status == args['status'])
    priority = parse_int_arg(args.get('priority'), 'Prioridade')
    if priority is not None:
        query = query.where(Task.priority == priority)
    user_id = parse_int_arg(args.get('user_id'), 'Usuário')
    if user_id is not None:
        query = query.where(Task.user_id == user_id)
    return [task.to_dict() for task in db.session.scalars(query.order_by(Task.id))]


def count_by_status():
    rows = db.session.execute(db.select(Task.status, func.count(Task.id)).group_by(Task.status))
    return dict(rows.all())


def count_overdue():
    return db.session.scalar(db.select(func.count(Task.id)).where(overdue_filter()))


def task_stats():
    by_status = count_by_status()
    total = sum(by_status.values())
    done = by_status.get(STATUS_DONE, 0)
    return {
        'total': total,
        'pending': by_status.get(STATUS_PENDING, 0),
        'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
        'done': done,
        'cancelled': by_status.get(STATUS_CANCELLED, 0),
        'overdue': count_overdue(),
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
