"""Carrega um PDF, divide o texto em chunks e grava os vetores no PostgreSQL."""

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    DATABASE_URL,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    PDF_PATH,
    COLLECTION_NAME,
)


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
    store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=DATABASE_URL,
        use_jsonb=True,
        pre_delete_collection=True,
    )
    store.add_documents(chunks)

    print(f"PDF: {PDF_PATH.name}")
    print(f"Páginas carregadas: {len(pages)}")
    print(f"Chunks gravados: {len(chunks)}")
    print(f"Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    main()
