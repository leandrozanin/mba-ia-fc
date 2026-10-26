from datetime import timedelta

from sqlalchemy import case, func

from controllers.task_controller import count_by_status, overdue_filter
from controllers.user_controller import get_user_or_404
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import (
    HIGH_PRIORITY_MAX,
    PRIORITY_NAMES,
    RECENT_ACTIVITY_DAYS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    VALID_STATUSES,
)
from utils.dates import utcnow


def _rate(part, total):
    return round((part / total) * 100, 2) if total > 0 else 0


def _count(model):
    return db.session.scalar(db.select(func.count()).select_from(model))


def _user_productivity():
    # Uma consulta agregada por usuário (antes: uma consulta de tasks por usuário).
    done = func.coalesce(func.sum(case((Task.status == STATUS_DONE, 1), else_=0)), 0)
    rows = db.session.execute(
        db.select(User.id, User.name, func.count(Task.id), done)
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    )
    return [
        {
            'user_id': user_id,
            'user_name': name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': _rate(completed, total),
        }
        for user_id, name, total, completed in rows
    ]


def summary_report():
    now = utcnow()
    by_status = count_by_status()
    by_priority = dict(db.session.execute(db.select(Task.priority, func.count(Task.id)).group_by(Task.priority)).all())

    overdue_tasks = db.session.scalars(db.select(Task).where(overdue_filter(now)).order_by(Task.id)).all()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    recent_created = db.session.scalar(db.select(func.count(Task.id)).where(Task.created_at >= since))
    recent_done = db.session.scalar(
        db.select(func.count(Task.id)).where(Task.status == STATUS_DONE, Task.updated_at >= since)
    )

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': sum(by_status.values()),
            'total_users': _count(User),
            'total_categories': _count(Category),
        },
        'tasks_by_status': {status: by_status.get(status, 0) for status in VALID_STATUSES},
        'tasks_by_priority': {name: by_priority.get(level, 0) for level, name in PRIORITY_NAMES.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_created,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': _user_productivity(),
    }


def user_report(user_id):
    user = get_user_or_404(user_id)
    tasks = db.session.scalars(db.select(Task).where(Task.user_id == user_id)).all()
    now = utcnow()

    counts = {status: 0 for status in VALID_STATUSES}
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': len(tasks),
            'done': counts[STATUS_DONE],
            'pending': counts[STATUS_PENDING],
            'in_progress': counts[STATUS_IN_PROGRESS],
            'cancelled': counts[STATUS_CANCELLED],
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': _rate(counts[STATUS_DONE], len(tasks)),
        },
    }
