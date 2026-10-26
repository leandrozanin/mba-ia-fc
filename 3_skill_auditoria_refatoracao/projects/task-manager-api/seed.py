"""Popula o banco configurado em DATABASE_URL com dados de exemplo.

Uso:
    python seed.py           # só popula se o banco estiver vazio
    python seed.py --reset   # apaga tasks, usuários e categorias antes de popular
"""
import os
import secrets
import sys
from datetime import timedelta

from app import create_app
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.dates import utcnow

USERS = [
    ('João Silva', 'joao@email.com', 'admin'),
    ('Maria Santos', 'maria@email.com', 'user'),
    ('Pedro Oliveira', 'pedro@email.com', 'manager'),
]

CATEGORIES = [
    ('Backend', 'Tarefas de backend', '#3498db'),
    ('Frontend', 'Tarefas de frontend', '#2ecc71'),
    ('DevOps', 'Tarefas de infraestrutura', '#e74c3c'),
    ('Bug', 'Correção de bugs', '#e67e22'),
]

# (título, descrição, status, prioridade, índice do usuário, índice da categoria, dias até o prazo, tags)
TASKS = [
    ('Implementar autenticação JWT', 'Adicionar autenticação real com JWT', 'pending', 1, 0, 0, -3, None),
    ('Criar tela de login', 'Tela de login responsiva', 'in_progress', 2, 1, 1, 5, None),
    ('Configurar CI/CD', 'Pipeline com GitHub Actions', 'done', 2, 2, 2, None, 'devops,ci,github'),
    ('Corrigir bug no filtro de busca', 'Filtro não funciona com caracteres especiais', 'pending', 1, 0, 3, -1, None),
    ('Adicionar paginação na API', 'Endpoints retornam todos os registros', 'pending', 3, 0, 0, 10, None),
    ('Escrever testes unitários', 'Cobertura mínima de 80%', 'pending', 2, 1, 0, None, None),
    ('Documentar API com Swagger', 'Gerar documentação automática', 'cancelled', 4, 2, 0, None, None),
    ('Refatorar models', 'Melhorar organização dos models', 'in_progress', 3, 1, 0, None, 'refactor,tech-debt'),
    ('Configurar monitoramento', 'Prometheus + Grafana', 'pending', 4, 2, 2, 20, None),
    ('Melhorar validações de input', 'Usar marshmallow ou pydantic', 'pending', 3, 0, 0, None, 'improvement,validation'),
]


def seed_data(reset=False):
    app = create_app()
    with app.app_context():
        if reset:
            db.session.execute(db.delete(Task))
            db.session.execute(db.delete(User))
            db.session.execute(db.delete(Category))
        elif db.session.scalar(db.select(db.func.count(User.id))):
            print('Banco já possui dados; use --reset para recriar.')
            return

        # Sem SEED_USER_PASSWORD cada conta recebe senha aleatória não divulgada.
        seed_password = os.environ.get('SEED_USER_PASSWORD')
        users = []
        for name, email, role in USERS:
            user = User(name=name, email=email, role=role)
            user.set_password(seed_password or secrets.token_urlsafe(16))
            users.append(user)
        categories = [Category(name=n, description=d, color=c) for n, d, c in CATEGORIES]
        db.session.add_all(users + categories)
        db.session.flush()

        now = utcnow()
        for title, description, status, priority, user_idx, cat_idx, due_in, tags in TASKS:
            db.session.add(Task(
                title=title,
                description=description,
                status=status,
                priority=priority,
                user_id=users[user_idx].id,
                category_id=categories[cat_idx].id,
                due_date=now + timedelta(days=due_in) if due_in is not None else None,
                tags=tags,
            ))
        db.session.commit()
        print(f'Seed concluído: {len(users)} usuários, {len(categories)} categorias, {len(TASKS)} tasks')


if __name__ == '__main__':
    seed_data(reset='--reset' in sys.argv)
