import logging

from sqlalchemy import func

from controllers.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError, commit
from controllers.validation import (
    require_payload,
    validate_bool,
    validate_email,
    validate_name,
    validate_password,
    validate_role,
)
from database import db
from models.constants import DEFAULT_ROLE
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)


def get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def list_users_with_task_count():
    counts = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .filter(Task.user_id.isnot(None))
        .group_by(Task.user_id)
        .all()
    )
    return [(user, counts.get(user.id, 0)) for user in User.query.order_by(User.id).all()]


def get_user_tasks(user_id):
    get_user_or_404(user_id)
    return Task.query.filter_by(user_id=user_id).order_by(Task.id).all()


def _ensure_email_available(email, user_id=None):
    existing = User.query.filter_by(email=email).first()
    if existing and existing.id != user_id:
        raise ConflictError('Email já cadastrado')


def create_user(data, current_user=None):
    require_payload(data)

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    validate_name(name)
    validate_email(email)
    validate_password(password)
    _ensure_email_available(email)
    validate_role(role)
    if role != DEFAULT_ROLE and not (current_user and current_user.is_admin()):
        raise ForbiddenError('Apenas administradores podem atribuir este papel')

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    commit('Erro ao criar usuário')
    logger.info('Usuário criado: id=%s', user.id)
    return user


def update_user(user_id, data, current_user):
    user = get_user_or_404(user_id)
    is_admin = current_user.is_admin()
    if not is_admin and current_user.id != user.id:
        raise ForbiddenError('Acesso negado')
    require_payload(data)

    if ('role' in data or 'active' in data) and not is_admin:
        raise ForbiddenError('Apenas administradores podem alterar papel ou status')

    changes = {}
    if 'name' in data:
        changes['name'] = validate_name(data['name'])
    if 'email' in data:
        changes['email'] = validate_email(data['email'])
        _ensure_email_available(data['email'], user.id)
    if 'password' in data:
        validate_password(data['password'], 'Senha muito curta')
    if 'role' in data:
        changes['role'] = validate_role(data['role'])
    if 'active' in data:
        changes['active'] = validate_bool(data['active'], 'active')

    for field, value in changes.items():
        setattr(user, field, value)
    if 'password' in data:
        user.set_password(data['password'])

    commit('Erro ao atualizar')
    logger.info('Usuário atualizado: id=%s', user.id)
    return user


def delete_user(user_id):
    user = get_user_or_404(user_id)
    # Tarefas e usuário saem na mesma transação.
    Task.query.filter_by(user_id=user_id).delete(synchronize_session='fetch')
    db.session.delete(user)
    commit('Erro ao deletar')
    logger.info('Usuário deletado: id=%s', user_id)
