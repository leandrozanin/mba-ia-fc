import math


def require_unit_score(value, metric_name):
    if isinstance(value, bool):
        raise ValueError(f"A nota de {metric_name} deve ser numérica entre 0 e 1.")
    try:
        score = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"A nota de {metric_name} deve ser numérica entre 0 e 1.") from error
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise ValueError(f"A nota de {metric_name} deve estar entre 0 e 1.")
    return score
