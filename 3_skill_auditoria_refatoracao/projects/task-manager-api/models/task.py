from database import db
from utils.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_PENDING
from utils.dates import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    def is_overdue(self, now=None):
        """Regra única: prazo vencido e task ainda aberta."""
        if not self.due_date or self.status in CLOSED_STATUSES:
            return False
        return self.due_date < (now or utcnow())

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

    def to_detail_dict(self):
        """Formato de GET /tasks/<id>: to_dict + overdue."""
        return {**self.to_dict(), 'overdue': self.is_overdue()}

    def to_list_dict(self):
        """Formato de GET /tasks: detalhe + nomes de usuário e categoria."""
        return {
            **self.to_detail_dict(),
            'user_name': self.user.name if self.user else None,
            'category_name': self.category.name if self.category else None,
        }

    def to_summary_dict(self):
        """Formato reduzido de GET /users/<id>/tasks."""
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
