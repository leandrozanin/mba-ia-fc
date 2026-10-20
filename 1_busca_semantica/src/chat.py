"""Interface de chat no terminal."""

from config import FALLBACK_ANSWER
from search import answer_question


def main() -> None:
    print("Chat com o PDF. Digite 'sair' para encerrar.")

    while True:
        try:
            question = input("\nPERGUNTA: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            break

        if question.lower() in {"sair", "exit", "quit"}:
            print("Até logo!")
            break
        if not question:
            continue

        try:
            answer = answer_question(question)
        except Exception as error:
            print(f"ERRO: {error}")
            print("Confira a conexão com o PostgreSQL, a ingestão do PDF e sua chave da OpenAI.")
            continue

        print(f"RESPOSTA: {answer or FALLBACK_ANSWER}")


if __name__ == "__main__":
    main()
