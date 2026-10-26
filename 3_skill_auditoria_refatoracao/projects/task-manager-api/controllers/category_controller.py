from sqlalchemy import func

from controllers.validators import validate_category
from database import db
from errors import NotFoundError
from models.category import Category
from models.task import Task


def _get_category_or_404(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    counts = dict(db.session.execute(db.select(Task.category_id, func.count(Task.id)).group_by(Task.category_id)).all())
    categories = db.session.scalars(db.select(Category).order_by(Category.id))
    return [{**category.to_dict(), 'task_count': counts.get(category.id, 0)} for category in categories]


def create_category(data):
    category = Category(**validate_category(data))
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(category_id, data):
    category = _get_category_or_404(category_id)
    for field, value in validate_category(data, partial=True).items():
        setattr(category, field, value)
    db.session.commit()
    return category.to_dict()


def delete_category(category_id):
    category = _get_category_or_404(category_id)
    # Política explícita: tasks da categoria ficam sem categoria, na mesma transação.
    db.session.execute(db.update(Task).where(Task.category_id == category_id).values(category_id=None))
    db.session.delete(category)
    db.session.commit()
