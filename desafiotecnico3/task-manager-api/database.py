from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class PersistenceMixin:
    """Persistência dos models; cada operação é uma transação (commit ou rollback)."""

    @classmethod
    def get_by_id(cls, entity_id):
        return db.session.get(cls, entity_id)

    @classmethod
    def count(cls, *conditions):
        return db.session.execute(db.select(db.func.count()).select_from(cls).where(*conditions)).scalar_one()

    def save(self):
        db.session.add(self)
        commit()
        return self

    def delete(self):
        db.session.delete(self)
        commit()


def commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
