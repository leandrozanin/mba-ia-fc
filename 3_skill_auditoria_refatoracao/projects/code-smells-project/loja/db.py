import logging
import sqlite3
from contextlib import contextmanager

from flask import current_app, g
from werkzeug.security import generate_password_hash

from .constants import TIPO_ADMIN

logger = logging.getLogger(__name__)

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
]

PRODUTOS_EXEMPLO = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def connect(path):
    # isolation_level=None: autocommit; transações de múltiplas escritas usam transacao()
    conexao = sqlite3.connect(path, isolation_level=None)
    conexao.row_factory = sqlite3.Row
    return conexao


def get_db():
    """Conexão por requisição, fechada no teardown do app context."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_erro=None):
    conexao = g.pop("db", None)
    if conexao is not None:
        conexao.close()


@contextmanager
def transacao(db):
    """Transação atômica: BEGIN IMMEDIATE bloqueia escritas concorrentes até o COMMIT."""
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except BaseException:
        db.execute("ROLLBACK")
        raise
    db.execute("COMMIT")


def init_db(config):
    conexao = connect(config["DATABASE"])
    try:
        with transacao(conexao):
            for ddl in SCHEMA:
                conexao.execute(ddl)
            if conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
                conexao.executemany(
                    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                    PRODUTOS_EXEMPLO,
                )
            _migrar_senhas_legadas(conexao)
            if config.get("ADMIN_EMAIL"):
                _garantir_admin(conexao, config["ADMIN_EMAIL"], config["ADMIN_PASSWORD"])
        _criar_indice_email_unico(conexao)
    finally:
        conexao.close()


def _migrar_senhas_legadas(conexao):
    """Converte senhas gravadas em texto puro por versões anteriores para hash."""
    linhas = conexao.execute("SELECT id, senha FROM usuarios WHERE senha IS NOT NULL").fetchall()
    legadas = [(linha["id"], linha["senha"]) for linha in linhas if not linha["senha"].startswith(PREFIXOS_HASH)]
    for usuario_id, senha in legadas:
        conexao.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (generate_password_hash(senha), usuario_id))
    if legadas:
        logger.info("Senhas legadas migradas para hash: %d usuário(s)", len(legadas))


def _garantir_admin(conexao, email, senha):
    existente = conexao.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    if existente is None:
        conexao.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            ("Admin", email, generate_password_hash(senha), TIPO_ADMIN),
        )
        logger.info("Usuário administrador inicial criado")


def _criar_indice_email_unico(conexao):
    try:
        conexao.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)")
    except sqlite3.IntegrityError:
        logger.warning("Há emails duplicados em usuarios; índice único não criado (unicidade validada na aplicação)")
