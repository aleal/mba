"""Validação de entrada compartilhada por criação e atualização (mesmas mensagens da API original)."""
import re

from config.constants import (
    DATE_FORMAT, DEFAULT_COLOR, DEFAULT_PRIORITY, DEFAULT_STATUS, EMAIL_PATTERN, PASSWORD_MIN_LENGTH,
    PRIORITY_MAX, PRIORITY_MIN, TASK_STATUSES, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH, USER_ROLES,
)
from middlewares.error_handler import ValidationError
from utils.dates import parse_date

_COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def require_payload(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def to_int(value):
    """Inteiro a partir de int ou string numérica; None se não for possível."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip('-').isdigit():
        return int(value)
    return None


def is_valid_email(email):
    return isinstance(email, str) and re.match(EMAIL_PATTERN, email) is not None


# --- tasks ---

def validate_task(data, partial):
    """Campos validados da task. `partial=True` (PUT) valida só o que veio no corpo."""
    require_payload(data)
    fields = {}

    if not partial or 'title' in data:
        title = data.get('title')
        if not title or not isinstance(title, str):
            raise ValidationError('Título é obrigatório')
        if len(title) < TITLE_MIN_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > TITLE_MAX_LENGTH:
            raise ValidationError('Título muito longo')
        fields['title'] = title

    if not partial or 'description' in data:
        fields['description'] = data.get('description', '')

    if not partial or 'status' in data:
        status = data.get('status', DEFAULT_STATUS)
        if status not in TASK_STATUSES:
            raise ValidationError('Status inválido')
        fields['status'] = status

    if not partial or 'priority' in data:
        priority = to_int(data.get('priority', DEFAULT_PRIORITY))
        if priority is None or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
            raise ValidationError('Prioridade deve ser entre 1 e 5')
        fields['priority'] = priority

    for key, label in (('user_id', 'user_id'), ('category_id', 'category_id')):
        if not partial or key in data:
            fields[key] = _optional_id(data.get(key), label)

    if 'due_date' in data or not partial:
        fields['due_date'] = _parse_due_date(data.get('due_date'), partial)

    if 'tags' in data or not partial:
        fields['tags'] = _parse_tags(data.get('tags'))

    return fields


def _optional_id(value, label):
    if not value:
        return None
    parsed = to_int(value)
    if parsed is None:
        raise ValidationError(f'{label} inválido')
    return parsed


def _parse_due_date(value, partial):
    if not value:
        return None
    parsed = parse_date(value, DATE_FORMAT)
    if parsed is None:
        raise ValidationError('Formato de data inválido' if partial else 'Formato de data inválido. Use YYYY-MM-DD')
    return parsed


def _parse_tags(tags):
    if not tags:
        return tags or None
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        return ','.join(tags)
    if isinstance(tags, str):
        return tags
    raise ValidationError('Tags inválidas')


def validate_search_filters(args):
    filters = {'text': args.get('q', ''), 'status': args.get('status', '')}
    for key, message in (('priority', 'Prioridade inválida'), ('user_id', 'user_id inválido')):
        raw = args.get(key, '')
        value = to_int(raw) if raw else None
        if raw and value is None:
            raise ValidationError(message)
        filters[key] = value
    return filters


# --- users ---

def validate_user_create(data):
    require_payload(data)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password or not isinstance(password, str):
        raise ValidationError('Senha é obrigatória')
    if not is_valid_email(email):
        raise ValidationError('Email inválido')
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    return {'name': name, 'email': email, 'password': password}


def validate_role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_user_update(data):
    require_payload(data)
    fields = {}
    if 'name' in data:
        if not data['name'] or not isinstance(data['name'], str):
            raise ValidationError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'email' in data:
        if not is_valid_email(data['email']):
            raise ValidationError('Email inválido')
        fields['email'] = data['email']
    if 'password' in data:
        if not isinstance(data['password'], str) or len(data['password']) < PASSWORD_MIN_LENGTH:
            raise ValidationError('Senha muito curta')
        fields['password'] = data['password']
    if 'role' in data:
        fields['role'] = validate_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active deve ser booleano')
        fields['active'] = data['active']
    return fields


def validate_login(data):
    require_payload(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')
    return email, password


# --- categories ---

def validate_category(data, partial):
    if partial:
        if not isinstance(data, dict):
            raise ValidationError('Dados inválidos')
    else:
        require_payload(data)
    fields = {}
    if not partial or 'name' in data:
        if not data.get('name') or not isinstance(data.get('name'), str):
            raise ValidationError('Nome é obrigatório')
        fields['name'] = data['name']
    if not partial or 'description' in data:
        fields['description'] = data.get('description', '')
    if not partial or 'color' in data:
        color = data.get('color', DEFAULT_COLOR)
        if not isinstance(color, str) or not _COLOR_PATTERN.match(color):
            raise ValidationError('Cor inválida')
        fields['color'] = color
    return fields
