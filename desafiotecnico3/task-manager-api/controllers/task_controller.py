import logging

from controllers.common import get_or_404
from controllers.validators import validate_search_filters, validate_task
from config.constants import DONE_STATUS, TASK_STATUSES
from middlewares.error_handler import NotFoundError
from models.category import Category
from models.task import Task, completion_rate
from models.user import User
from utils.dates import utcnow

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'


class TaskController:
    def __init__(self, notifier):
        self.notifier = notifier

    def list_tasks(self):
        now = utcnow()
        result = []
        for task in Task.all_with_relations():
            data = task.to_dict()
            data['overdue'] = task.is_overdue(now)
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
            result.append(data)
        return result, 200

    def get_task(self, task_id):
        task = get_or_404(Task, task_id, TASK_NOT_FOUND)
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data, 200

    def create_task(self, data):
        fields = validate_task(data, partial=False)
        self._ensure_references_exist(fields)
        task = Task(**fields).save()
        logger.info('task criada id=%s', task.id)
        if task.user:
            self.notifier.notify_task_assigned(task.user, task)
        return task.to_dict(), 201

    def update_task(self, task_id, data):
        task = get_or_404(Task, task_id, TASK_NOT_FOUND)
        fields = validate_task(data, partial=True)
        self._ensure_references_exist(fields)
        previous_user_id = task.user_id
        for key, value in fields.items():
            setattr(task, key, value)
        task.updated_at = utcnow()
        task.save()
        logger.info('task atualizada id=%s', task.id)
        if task.user and task.user_id != previous_user_id:
            self.notifier.notify_task_assigned(task.user, task)
        return task.to_dict(), 200

    def delete_task(self, task_id):
        task = get_or_404(Task, task_id, TASK_NOT_FOUND)
        task.delete()
        logger.info('task deletada id=%s', task_id)
        return {'message': 'Task deletada com sucesso'}, 200

    def search_tasks(self, args):
        filters = validate_search_filters(args)
        return [task.to_dict() for task in Task.search(**filters)], 200

    def stats(self):
        by_status = Task.count_by_status()
        total = Task.count()
        done = by_status.get(DONE_STATUS, 0)
        stats = {status: by_status.get(status, 0) for status in TASK_STATUSES}
        stats.update({
            'total': total,
            'overdue': Task.count(*Task.overdue_conditions(utcnow())),
            'completion_rate': completion_rate(done, total),
        })
        return stats, 200

    @staticmethod
    def _ensure_references_exist(fields):
        if fields.get('user_id') and User.get_by_id(fields['user_id']) is None:
            raise NotFoundError('Usuário não encontrado')
        if fields.get('category_id') and Category.get_by_id(fields['category_id']) is None:
            raise NotFoundError('Categoria não encontrada')
