import logging

from controllers.common import get_or_404
from controllers.validators import validate_login, validate_role, validate_user_create, validate_user_update
from config.constants import DEFAULT_ROLE
from middlewares.error_handler import ConflictError, ForbiddenError, UnauthorizedError
from models.task import Task
from models.user import User

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'


def _is_admin(actor):
    return actor is not None and actor.is_admin()


class UserController:
    def __init__(self, token_service):
        self.token_service = token_service

    def list_users(self):
        result = []
        for user, task_count, _done in User.all_with_task_stats():
            data = user.to_dict()
            data['task_count'] = task_count
            result.append(data)
        return result, 200

    def get_user(self, user_id):
        user = get_or_404(User, user_id, USER_NOT_FOUND)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in Task.by_user(user_id)]
        return data, 200

    def create_user(self, data, actor=None):
        fields = validate_user_create(data)
        if User.find_by_email(fields['email']):
            raise ConflictError('Email já cadastrado')
        role = validate_role(data.get('role', DEFAULT_ROLE))
        if role != DEFAULT_ROLE and not _is_admin(actor):
            raise ForbiddenError('Apenas administradores podem definir o role')

        user = User(name=fields['name'], email=fields['email'], role=role)
        user.set_password(fields['password'])
        user.save()
        logger.info('usuário criado id=%s', user.id)
        return user.to_dict(), 201

    def update_user(self, user_id, data, actor=None):
        user = get_or_404(User, user_id, USER_NOT_FOUND)
        fields = validate_user_update(data)
        if 'email' in fields:
            existing = User.find_by_email(fields['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
        if ('role' in fields or 'active' in fields) and not _is_admin(actor):
            raise ForbiddenError('Apenas administradores podem alterar role ou status')

        password = fields.pop('password', None)
        for key, value in fields.items():
            setattr(user, key, value)
        if password is not None:
            user.set_password(password)
        user.save()
        return user.to_dict(), 200

    def delete_user(self, user_id):
        user = get_or_404(User, user_id, USER_NOT_FOUND)
        user.delete_with_tasks()
        logger.info('usuário deletado id=%s', user_id)
        return {'message': 'Usuário deletado com sucesso'}, 200

    def list_user_tasks(self, user_id):
        get_or_404(User, user_id, USER_NOT_FOUND)
        return [task.to_summary_dict() for task in Task.by_user(user_id)], 200

    def login(self, data):
        email, password = validate_login(data)
        user = User.find_by_email(email)
        if user is None or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        if user.has_legacy_password_hash():
            user.set_password(password)  # migra o hash MD5 legado no primeiro login válido
            user.save()
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self.token_service.issue(user.id),
        }, 200
