import json
from collections import Counter


EXPECTED_DATASET_SIZE = 15


def validate_dataset_examples(examples, expected_count=EXPECTED_DATASET_SIZE):
    if not isinstance(examples, list):
        raise ValueError("O dataset deve ser uma lista de exemplos.")
    if len(examples) != expected_count:
        raise ValueError(
            f"Dataset inválido: esperados {expected_count} exemplos, recebidos {len(examples)}."
        )

    for index, example in enumerate(examples, 1):
        if not isinstance(example, dict):
            raise ValueError(f"Exemplo {index} deve ser um objeto JSON.")
        inputs = example.get("inputs")
        outputs = example.get("outputs")
        has_report = (
            isinstance(inputs, dict)
            and isinstance(inputs.get("bug_report"), str)
            and bool(inputs["bug_report"].strip())
        )
        if not has_report:
            raise ValueError(f"Exemplo {index} precisa de inputs.bug_report não vazio.")
        has_reference = (
            isinstance(outputs, dict)
            and isinstance(outputs.get("reference"), str)
            and bool(outputs["reference"].strip())
        )
        if not has_reference:
            raise ValueError(f"Exemplo {index} precisa de outputs.reference não vazio.")


def _example_key(inputs, outputs):
    return json.dumps([inputs, outputs], ensure_ascii=False, sort_keys=True)


def dataset_matches_examples(remote_examples, source_examples):
    remote_payloads = [
        _example_key(example.inputs, example.outputs)
        for example in remote_examples
    ]
    source_payloads = [
        _example_key(example.get("inputs"), example.get("outputs"))
        for example in source_examples
    ]
    return Counter(remote_payloads) == Counter(source_payloads)
