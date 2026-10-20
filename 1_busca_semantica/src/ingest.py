"""Carrega um PDF, divide o texto em chunks e grava os vetores no PostgreSQL."""

import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    ACTIVE_COLLECTION_FILE,
    DATABASE_URL,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    PDF_PATH,
    COLLECTION_NAME,
    active_collection_name,
)
from collection_state import activate_collection


def main() -> None:
    if not PDF_PATH.is_file():
        raise FileNotFoundError(
            f"PDF não encontrado: {PDF_PATH}. Defina PDF_PATH no arquivo .env."
        )

    pages = PyPDFLoader(str(PDF_PATH)).load()
    if not any(page.page_content.strip() for page in pages):
        raise ValueError(f"Nenhum texto foi extraído do PDF: {PDF_PATH}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(pages)
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS,
    )

    # A ingestão substitui a collection para não duplicar os chunks em reexecuções.
    previous_collection = active_collection_name()
    staging_collection = f"{COLLECTION_NAME[:42]}_stg_{uuid.uuid4().hex[:16]}"
    store = PGVector(
        embeddings=embeddings,
        collection_name=staging_collection,
        connection=DATABASE_URL,
        use_jsonb=True,
    )
    try:
        store.add_documents(chunks)
        activate_collection(staging_collection, ACTIVE_COLLECTION_FILE)
    except Exception:
        try:
            store.delete_collection()
        except Exception:
            pass
        raise

    if previous_collection != staging_collection:
        try:
            previous_store = PGVector(
                embeddings=embeddings,
                collection_name=previous_collection,
                connection=DATABASE_URL,
                use_jsonb=True,
            )
            previous_store.delete_collection()
        except Exception as error:
            print(f"Aviso: collection antiga não removida: {error}")

    print(f"PDF: {PDF_PATH.name}")
    print(f"Páginas carregadas: {len(pages)}")
    print(f"Chunks gravados: {len(chunks)}")
    print(f"Collection: {staging_collection}")


if __name__ == "__main__":
    main()
