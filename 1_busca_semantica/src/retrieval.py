import math


def filter_by_max_distance(matches, max_distance: float):
    if not math.isfinite(max_distance) or max_distance < 0:
        raise ValueError("SEARCH_MAX_DISTANCE deve ser um número finito não negativo.")

    return [
        (document, distance)
        for document, distance in matches
        if math.isfinite(distance) and distance <= max_distance
    ]


def retrieve_context(vector_store, question: str, k: int, max_distance: float) -> str:
    matches = vector_store.similarity_search_with_score(question, k=k)
    relevant_matches = filter_by_max_distance(matches, max_distance)
    return "\n\n---\n\n".join(
        document.page_content for document, _ in relevant_matches
    )
