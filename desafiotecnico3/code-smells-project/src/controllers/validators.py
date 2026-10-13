from src.errors import ValidationError


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_positive_int(value):
    return is_int(value) and value > 0


def require_dict(dados, message="Dados inválidos"):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError(message)
    return dados


def optional_float(value, campo):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        raise ValidationError(f"{campo} inválido") from None
