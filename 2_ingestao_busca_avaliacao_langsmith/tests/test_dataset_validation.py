import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dataset_validation import dataset_matches_examples, validate_dataset_examples


def example(report="Broken login", reference="Login succeeds"):
    return {"inputs": {"bug_report": report}, "outputs": {"reference": reference}}


class DatasetValidationTests(unittest.TestCase):
    def test_accepts_the_expected_number_of_complete_examples(self):
        examples = [example(f"Bug {index}", f"Reference {index}") for index in range(15)]

        validate_dataset_examples(examples)

    def test_rejects_a_dataset_with_the_wrong_count(self):
        with self.assertRaisesRegex(ValueError, "15"):
            validate_dataset_examples([example()])

    def test_rejects_examples_missing_evaluation_fields(self):
        with self.assertRaisesRegex(ValueError, "reference"):
            validate_dataset_examples([{"inputs": {"bug_report": "Broken login"}, "outputs": {}}], expected_count=1)

    def test_existing_dataset_must_match_source_examples(self):
        source = [example("Bug A", "Reference A"), example("Bug B", "Reference B")]
        matching = [
            SimpleNamespace(inputs={"bug_report": "Bug B"}, outputs={"reference": "Reference B"}),
            SimpleNamespace(inputs={"bug_report": "Bug A"}, outputs={"reference": "Reference A"}),
        ]
        stale = [
            SimpleNamespace(inputs={"bug_report": "Bug A"}, outputs={"reference": "Reference A"}),
            SimpleNamespace(inputs={"bug_report": "Bug B"}, outputs={"reference": "Different reference"}),
        ]

        self.assertTrue(dataset_matches_examples(matching, source))
        self.assertFalse(dataset_matches_examples(stale, source))


if __name__ == "__main__":
    unittest.main()
