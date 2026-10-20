import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from evaluation_validation import require_unit_score


class EvaluationValidationTests(unittest.TestCase):
    def test_rejects_scores_outside_zero_to_one(self):
        with self.assertRaises(ValueError):
            require_unit_score(1.2, "clarity")

    def test_rejects_non_finite_scores(self):
        with self.assertRaises(ValueError):
            require_unit_score(float("nan"), "clarity")


if __name__ == "__main__":
    unittest.main()
