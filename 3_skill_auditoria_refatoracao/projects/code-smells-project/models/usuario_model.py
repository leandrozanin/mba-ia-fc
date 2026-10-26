from werkzeug.security import check_password_hash, generate_password_hash

from models.database import get_db

CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")


def _to_dict(row):
    # A senha nunca sai do model.
    return {campo: row[campo] for campo in CAMPOS_PUBLICOS}


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_dict(row) if row else None


def email_existe(email):
    return get_db().execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone() is not None


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid


def autenticar(email, senha):
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None or not check_password_hash(row["senha"], senha):
        return None
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}


def contar():
    return get_db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
