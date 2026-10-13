from database import db, PersistenceMixin
from config.constants import DEFAULT_COLOR
from utils.dates import utcnow


class Category(PersistenceMixin, db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    @classmethod
    def all_with_task_counts(cls):
        from models.task import Task
        stmt = (
            db.select(cls, db.func.count(Task.id))
            .outerjoin(Task, Task.category_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(stmt).all()

    def delete_detaching_tasks(self):
        """Desvincula as tasks da categoria e a apaga na mesma transação (sem category_id órfão)."""
        from models.task import Task
        db.session.execute(
            db.update(Task).where(Task.category_id == self.id).values(category_id=None)
        )
        self.delete()
