import os
import uuid
from pathlib import Path


def read_active_collection(default_name: str, pointer_file: Path) -> str:
    try:
        active_name = pointer_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return default_name
    return active_name or default_name


def activate_collection(collection_name: str, pointer_file: Path) -> None:
    if not collection_name.strip():
        raise ValueError("O nome da collection ativa não pode ficar vazio.")

    pointer_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = pointer_file.with_name(
        f"{pointer_file.name}.{uuid.uuid4().hex}.tmp"
    )
    try:
        temporary_file.write_text(collection_name, encoding="utf-8")
        os.replace(temporary_file, pointer_file)
    finally:
        temporary_file.unlink(missing_ok=True)
