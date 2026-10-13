from middlewares.error_handler import NotFoundError


def get_or_404(model, entity_id, message):
    entity = model.get_by_id(entity_id)
    if entity is None:
        raise NotFoundError(message)
    return entity
