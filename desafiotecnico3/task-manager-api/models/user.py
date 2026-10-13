import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from database import db, PersistenceMixin
from config.constants import ADMIN_ROLE, DEFAULT_ROLE, DONE_STATUS
from utils.dates import utcnow

_LEGACY_MD5_LENGTH = 32


class User(PersistenceMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        # A senha (hash) nunca sai do model.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if self.has_legacy_password_hash():
            legacy = hashlib.md5(raw_password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, raw_password)

    def has_legacy_password_hash(self):
        """Hashes MD5 gravados pela versão antiga; são regravados no próximo login válido."""
        return len(self.password or '') == _LEGACY_MD5_LENGTH and ':' not in self.password

    def is_admin(self):
        return self.role == ADMIN_ROLE

    # --- consultas ---

    @classmethod
    def all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def find_by_email(cls, email):
        return db.session.execute(db.select(cls).filter_by(email=email)).scalar_one_or_none()

    @classmethod
    def all_with_task_stats(cls):
        """(user, total_tasks, done_tasks) para todos os usuários, em uma query."""
        from models.task import Task
        done = db.func.coalesce(db.func.sum(db.case((Task.status == DONE_STATUS, 1), else_=0)), 0)
        stmt = (
            db.select(cls, db.func.count(Task.id), done)
            .outerjoin(Task, Task.user_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(stmt).all()

    def delete_with_tasks(self):
        """Apaga o usuário e as tasks dele na mesma transação."""
        from models.task import Task
        Task.delete_by_user(self.id)
        self.delete()
