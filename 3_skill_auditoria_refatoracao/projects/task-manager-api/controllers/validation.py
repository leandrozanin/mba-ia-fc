import re
from datetime import datetime

from controllers.errors import ValidationError
from models.constants import (
    DATE_FORMAT,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    TASK_STATUSES,
    USER_ROLES,
)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def require_payload(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError('Dados inválidos')
    return data


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def validate_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return status


def validate_priority(priority):
    if not _is_int(priority):
        raise ValidationError('Prioridade inválida')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre %d e %d' % (MIN_PRIORITY, MAX_PRIORITY))
    return priority


def parse_int(value, message):
    """Aceita int ou string numérica (query string, JSON legado); rejeita bool e o resto."""
    if _is_int(value):
        return value
    if isinstance(value, str) and value.strip().lstrip('-').isdigit():
        return int(value)
    raise ValidationError(message)


def parse_due_date(value):
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD') from None


def normalize_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return ','.join(tags)
    if isinstance(tags, str):
        return tags
    raise ValidationError('Tags inválidas')


def validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise ValidationError('Nome é obrigatório')
    return name


def validate_email(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValidationError('Email inválido')
    return email


def validate_password(password, message=None):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message or 'Senha deve ter no mínimo %d caracteres' % MIN_PASSWORD_LENGTH)
    return password


def validate_role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_bool(value, field):
    if not isinstance(value, bool):
        raise ValidationError('Campo %s deve ser booleano' % field)
    return value


def validate_color(color):
    if not isinstance(color, str) or not COLOR_PATTERN.match(color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color


def validate_optional_text(value, field):
    if value is not None and not isinstance(value, str):
        raise ValidationError('Campo %s deve ser texto' % field)
    return value
