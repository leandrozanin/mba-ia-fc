from ..constants import TIPO_CLIENTE

CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")


def _publico(row):
    """Serialização sem a coluna senha."""
    return {campo: row[campo] for campo in CAMPOS_PUBLICOS}


def listar(db):
    return [_publico(row) for row in db.execute("SELECT * FROM usuarios")]


def buscar_por_id(db, usuario_id):
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _publico(row) if row else None


def buscar_credenciais_por_email(db, email):
    """Retorna id, nome, email, tipo e o hash da senha, para uso exclusivo da autenticação."""
    row = db.execute("SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def email_existe(db, email):
    return db.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone() is not None


def criar(db, nome, email, senha_hash, tipo=TIPO_CLIENTE):
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    return cursor.lastrowid


def contar(db):
    return db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
