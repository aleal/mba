from collections import Counter

from database import db, PersistenceMixin
from config.constants import (
    CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_STATUS, DONE_STATUS, HIGH_PRIORITY_MAX, PRIORITY_LABELS,
    TASK_STATUSES,
)
from utils.dates import utcnow


class Task(PersistenceMixin, db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_summary_dict(self):
        """Formato reduzido usado em GET /users/<id>/tasks."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES

    def days_overdue(self, now=None):
        return ((now or utcnow()) - self.due_date).days

    # --- consultas ---

    @classmethod
    def all_with_relations(cls):
        stmt = db.select(cls).options(db.joinedload(cls.user), db.joinedload(cls.category)).order_by(cls.id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def by_user(cls, user_id):
        stmt = db.select(cls).filter_by(user_id=user_id).order_by(cls.id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        stmt = db.select(cls)
        if text:
            pattern = f'%{text}%'
            stmt = stmt.where(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            stmt = stmt.where(cls.status == status)
        if priority is not None:
            stmt = stmt.where(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return db.session.execute(stmt.order_by(cls.id)).scalars().all()

    @classmethod
    def count_by_status(cls):
        rows = db.session.execute(db.select(cls.status, db.func.count(cls.id)).group_by(cls.status)).all()
        return dict(rows)

    @classmethod
    def count_by_priority_label(cls):
        rows = dict(db.session.execute(db.select(cls.priority, db.func.count(cls.id)).group_by(cls.priority)).all())
        return {label: rows.get(priority, 0) for priority, label in PRIORITY_LABELS.items()}

    @classmethod
    def overdue_conditions(cls, now):
        return (cls.due_date.is_not(None), cls.due_date < now, cls.status.not_in(CLOSED_STATUSES))

    @classmethod
    def overdue(cls, now=None):
        stmt = db.select(cls).where(*cls.overdue_conditions(now or utcnow())).order_by(cls.id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def delete_by_user(cls, user_id):
        """Apaga as tasks do usuário em lote; o commit fica com quem chama (mesma transação)."""
        db.session.execute(db.delete(cls).where(cls.user_id == user_id))


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


def task_statistics(tasks, now=None):
    """Contagens por status, atrasadas e de alta prioridade de uma lista de tasks."""
    now = now or utcnow()
    by_status = Counter(task.status for task in tasks)
    total = len(tasks)
    return {
        'total_tasks': total,
        **{status: by_status[status] for status in TASK_STATUSES},
        'overdue': sum(1 for task in tasks if task.is_overdue(now)),
        'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
        'completion_rate': completion_rate(by_status[DONE_STATUS], total),
    }
