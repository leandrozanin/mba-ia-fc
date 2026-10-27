from datetime import timedelta

from sqlalchemy import case, func

from controllers.task_controller import count_by_status
from controllers.user_controller import get_user_or_404
from database import db
from models.category import Category
from models.constants import (
    DONE_STATUS,
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
)
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, utc_now


def _overdue_tasks(now):
    tasks = Task.query.filter(Task.overdue_filter(now)).order_by(Task.id).all()
    return [
        {
            'id': t.id,
            'title': t.title,
            'due_date': str(t.due_date),
            'days_overdue': (now - t.due_date).days,
        }
        for t in tasks
    ]


def _user_productivity():
    totals = {
        user_id: (total, completed or 0)
        for user_id, total, completed in db.session.query(
            Task.user_id,
            func.count(Task.id),
            func.sum(case((Task.status == DONE_STATUS, 1), else_=0)),
        )
        .filter(Task.user_id.isnot(None))
        .group_by(Task.user_id)
        .all()
    }
    stats = []
    for user in User.query.order_by(User.id).all():
        total, completed = totals.get(user.id, (0, 0))
        stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })
    return stats


def summary_report():
    now = utc_now()
    by_status, total_tasks = count_by_status()
    by_priority = dict(db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all())
    overdue = _overdue_tasks(now)
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': User.query.count(),
            'total_categories': Category.query.count(),
        },
        'tasks_by_status': by_status,
        'tasks_by_priority': {label: by_priority.get(p, 0) for p, label in PRIORITY_LABELS.items()},
        'overdue': {'count': len(overdue), 'tasks': overdue},
        'recent_activity': {
            'tasks_created_last_7_days': Task.query.filter(Task.created_at >= since).count(),
            'tasks_completed_last_7_days': Task.query.filter(
                Task.status == DONE_STATUS, Task.updated_at >= since
            ).count(),
        },
        'user_productivity': _user_productivity(),
    }


def user_report(user_id):
    user = get_user_or_404(user_id)
    tasks = Task.query.filter_by(user_id=user_id).all()
    now = utc_now()

    counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
    for t in tasks:
        if t.status in counts:
            counts[t.status] += 1

    total = len(tasks)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **counts,
            'overdue': sum(1 for t in tasks if t.is_overdue(now)),
            'high_priority': sum(1 for t in tasks if t.priority is not None and t.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(counts[DONE_STATUS], total),
        },
    }
