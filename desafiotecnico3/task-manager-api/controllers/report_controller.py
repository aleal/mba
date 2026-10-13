from datetime import timedelta

from controllers.common import get_or_404
from config.constants import DONE_STATUS, RECENT_ACTIVITY_DAYS, TASK_STATUSES
from models.category import Category
from models.task import Task, completion_rate, task_statistics
from models.user import User
from utils.dates import utcnow


class ReportController:
    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = Task.count_by_status()
        overdue_tasks = Task.overdue(now)

        report = {
            'generated_at': str(now),
            'overview': {
                'total_tasks': Task.count(),
                'total_users': User.count(),
                'total_categories': Category.count(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
            'tasks_by_priority': Task.count_by_priority_label(),
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'due_date': str(task.due_date),
                        'days_overdue': task.days_overdue(now),
                    }
                    for task in overdue_tasks
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': Task.count(Task.created_at >= since),
                'tasks_completed_last_7_days': Task.count(Task.status == DONE_STATUS, Task.updated_at >= since),
            },
            'user_productivity': [
                {
                    'user_id': user.id,
                    'user_name': user.name,
                    'total_tasks': total,
                    'completed_tasks': done,
                    'completion_rate': completion_rate(done, total),
                }
                for user, total, done in User.all_with_task_stats()
            ],
        }
        return report, 200

    def user_report(self, user_id):
        user = get_or_404(User, user_id, 'Usuário não encontrado')
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': task_statistics(Task.by_user(user_id)),
        }, 200
