import logging

from sqlalchemy import func

from controllers.errors import NotFoundError, ValidationError, commit
from controllers.validation import require_payload, validate_color, validate_name, validate_optional_text
from database import db
from models.category import Category
from models.constants import DEFAULT_COLOR
from models.task import Task

logger = logging.getLogger(__name__)


def get_category_or_404(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories_with_task_count():
    counts = dict(
        db.session.query(Task.category_id, func.count(Task.id))
        .filter(Task.category_id.isnot(None))
        .group_by(Task.category_id)
        .all()
    )
    return [(c, counts.get(c.id, 0)) for c in Category.query.order_by(Category.id).all()]


def create_category(data):
    require_payload(data)
    if not data.get('name'):
        raise ValidationError('Nome é obrigatório')

    category = Category(
        name=validate_name(data['name']),
        description=validate_optional_text(data.get('description', ''), 'description'),
        color=validate_color(data.get('color', DEFAULT_COLOR)),
    )
    db.session.add(category)
    commit('Erro ao criar categoria')
    logger.info('Categoria criada: id=%s', category.id)
    return category


def update_category(category_id, data):
    category = get_category_or_404(category_id)
    require_payload(data)

    changes = {}
    if 'name' in data:
        changes['name'] = validate_name(data['name'])
    if 'description' in data:
        changes['description'] = validate_optional_text(data['description'], 'description')
    if 'color' in data:
        changes['color'] = validate_color(data['color'])

    for field, value in changes.items():
        setattr(category, field, value)
    commit('Erro ao atualizar')
    return category


def delete_category(category_id):
    category = get_category_or_404(category_id)
    # O relacionamento Category.tasks zera category_id das tarefas vinculadas (comportamento original).
    db.session.delete(category)
    commit('Erro ao deletar')
    logger.info('Categoria deletada: id=%s', category_id)
