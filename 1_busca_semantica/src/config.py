"""Configurações compartilhadas pela ingestão e pelo chat."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def project_path(value: str) -> Path:
    """Resolve caminhos relativos a partir da pasta do projeto."""
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


PDF_PATH = project_path(os.getenv("PDF_PATH", "./document.pdf"))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/busca_semantica",
)
COLLECTION_NAME = os.getenv("PGVECTOR_COLLECTION", "pdf_busca_semantica")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536"))
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
FALLBACK_ANSWER = "Não tenho informações necessárias para responder sua pergunta."
