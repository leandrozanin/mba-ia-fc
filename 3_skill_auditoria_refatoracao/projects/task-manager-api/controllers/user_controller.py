import logging

from sqlalchemy import func

from controllers.validators import require_body, validate_user
from database import db
from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.task import Task
from models.user import User
from services.auth_service import issue_token
from utils.constants import ROLE_USER

logger = logging.getLogger(__name__)


def get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


def _email_taken(email, except_id=None):
    existing = db.session.scalar(db.select(User).where(User.email == email))
    return existing is not None and existing.id != except_id


def list_users():
    counts = dict(db.session.execute(db.select(Task.user_id, func.count(Task.id)).group_by(Task.user_id)).all())
    users = db.session.scalars(db.select(User).order_by(User.id))
    return [{**user.to_dict(), 'task_count': counts.get(user.id, 0)} for user in users]


def get_user(user_id):
    user = get_user_or_404(user_id)
    tasks = db.session.scalars(db.select(Task).where(Task.user_id == user_id).order_by(Task.id))
    return {**user.to_dict(), 'tasks': [task.to_dict() for task in tasks]}


def create_user(data, actor=None):
    fields = validate_user(data)
    if _email_taken(fields['email']):
        raise ConflictError('Email já cadastrado')

    role = fields.get('role', ROLE_USER)
    if role != ROLE_USER and not (actor and actor.is_admin()):
        raise ForbiddenError('Apenas admin pode definir role')

    user = User(name=fields['name'], email=fields['email'], role=role)
    user.set_password(fields['password'])
    db.session.add(user)
    db.session.commit()
    logger.info('Usuário criado: id=%s', user.id)
    return user.to_dict()


def update_user(user_id, data, actor):
    user = get_user_or_404(user_id)
    fields = validate_user(data, partial=True)

    if not actor.is_admin():
        if actor.id != user.id:
            raise ForbiddenError('Permissão insuficiente')
        if 'role' in fields or 'active' in fields:
            raise ForbiddenError('Apenas admin pode alterar role ou active')

    if 'email' in fields and _email_taken(fields['email'], except_id=user.id):
        raise ConflictError('Email já cadastrado')
    if 'password' in fields:
        user.set_password(fields.pop('password'))
    for field, value in fields.items():
        setattr(user, field, value)

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = get_user_or_404(user_id)
    # Mantém a regra original: as tasks do usuário saem junto, na mesma transação.
    db.session.execute(db.delete(Task).where(Task.user_id == user_id))
    db.session.delete(user)
    db.session.commit()
    logger.info('Usuário deletado: id=%s', user_id)


def get_user_tasks(user_id):
    get_user_or_404(user_id)
    tasks = db.session.scalars(db.select(Task).where(Task.user_id == user_id).order_by(Task.id))
    return [task.to_summary_dict() for task in tasks]


def login(data):
    require_body(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Dados inválidos')

    user = db.session.scalar(db.select(User).where(User.email == email))
    if user is None or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    db.session.commit()  # persiste o rehash de senhas MD5 legadas
    return {'message': 'Login realizado com sucesso', 'user': user.to_dict(), 'token': issue_token(user)}
