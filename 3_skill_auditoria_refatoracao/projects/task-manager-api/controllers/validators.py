"""Validação única por entidade, usada em create e update (partial)."""
import re
from datetime import datetime

from errors import ValidationError
from utils.constants import (
    DATE_FORMAT,
    DEFAULT_COLOR,
    DEFAULT_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_TITLE_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    STATUS_PENDING,
    VALID_ROLES,
    VALID_STATUSES,
)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def require_body(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError('Dados inválidos')
    return data


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _optional_id(value, label):
    if value in (None, 0):
        return None
    if not _is_int(value):
        raise ValidationError(f'{label} inválido')
    return value


def parse_int_arg(value, label):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f'{label} inválido') from None


def validate_task(data, partial=False):
    require_body(data)
    result = {}

    if 'title' in data or not partial:
        title = data.get('title')
        if not title:
            raise ValidationError('Título é obrigatório')
        if not isinstance(title, str):
            raise ValidationError('Título inválido')
        if len(title) < MIN_TITLE_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError('Título muito longo')
        result['title'] = title

    if 'description' in data or not partial:
        description = data.get('description', '')
        if description is not None and not isinstance(description, str):
            raise ValidationError('Descrição inválida')
        result['description'] = description

    if 'status' in data or not partial:
        status = data.get('status', STATUS_PENDING)
        if status not in VALID_STATUSES:
            raise ValidationError('Status inválido')
        result['status'] = status

    if 'priority' in data or not partial:
        priority = data.get('priority', DEFAULT_PRIORITY)
        if not _is_int(priority) or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
            raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
        result['priority'] = priority

    for field, label in (('user_id', 'Usuário'), ('category_id', 'Categoria')):
        if field in data or not partial:
            result[field] = _optional_id(data.get(field), label)

    if 'due_date' in data:
        due_date = data['due_date']
        if due_date:
            try:
                result['due_date'] = datetime.strptime(due_date, DATE_FORMAT)
            except (TypeError, ValueError):
                raise ValidationError('Formato de data inválido. Use YYYY-MM-DD') from None
        else:
            result['due_date'] = None

    if 'tags' in data:
        tags = data['tags']
        if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
            result['tags'] = ','.join(tags) or None
        elif isinstance(tags, str) or tags is None:
            result['tags'] = tags or None
        else:
            raise ValidationError('Tags inválidas')

    return result


def validate_user(data, partial=False):
    require_body(data)
    result = {}

    if 'name' in data or not partial:
        name = data.get('name')
        if not isinstance(name, str) or not name.strip():
            raise ValidationError('Nome é obrigatório')
        result['name'] = name.strip()

    if 'email' in data or not partial:
        email = data.get('email')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
            raise ValidationError('Email inválido')
        result['email'] = email

    if 'password' in data or not partial:
        password = data.get('password')
        if not password:
            raise ValidationError('Senha é obrigatória')
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        result['password'] = password

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            raise ValidationError('Role inválido')
        result['role'] = data['role']

    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active deve ser booleano')
        result['active'] = data['active']

    return result


def validate_category(data, partial=False):
    require_body(data)
    result = {}

    if 'name' in data or not partial:
        name = data.get('name')
        if not isinstance(name, str) or not name.strip():
            raise ValidationError('Nome é obrigatório')
        result['name'] = name.strip()

    if 'description' in data or not partial:
        description = data.get('description', '')
        if description is not None and not isinstance(description, str):
            raise ValidationError('Descrição inválida')
        result['description'] = description

    if 'color' in data or not partial:
        color = data.get('color', DEFAULT_COLOR)
        if not isinstance(color, str) or not COLOR_PATTERN.match(color):
            raise ValidationError('Cor inválida. Use #RRGGBB')
        result['color'] = color

    return result
