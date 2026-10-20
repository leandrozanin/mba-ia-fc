"""Configurações compartilhadas pela ingestão e pelo chat."""

import math
import os
from pathlib import Path

from collection_state import read_active_collection
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
ACTIVE_COLLECTION_FILE = PROJECT_ROOT / ".active_pgvector_collection"
SEARCH_MAX_DISTANCE = float(os.getenv("SEARCH_MAX_DISTANCE", "0.5"))
if not math.isfinite(SEARCH_MAX_DISTANCE) or SEARCH_MAX_DISTANCE < 0:
    raise ValueError("SEARCH_MAX_DISTANCE deve ser um número finito não negativo.")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536"))
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
FALLBACK_ANSWER = "Não tenho informações necessárias para responder sua pergunta."


def active_collection_name() -> str:
    return read_active_collection(COLLECTION_NAME, ACTIVE_COLLECTION_FILE)
