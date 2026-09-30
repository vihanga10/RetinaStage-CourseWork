import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from guide import answer, review_rule


class GuideTests(unittest.TestCase):
    def test_confidence_and_gap_review(self):
        self.assertTrue(review_rule([.10, .28, .29, .14, .19])[0])
        self.assertFalse(review_rule([.92, .02, .02, .02, .02])[0])
        flag, reasons = review_rule([.46, .02, .01, .45, .06])
        self.assertTrue(flag)
        self.assertEqual(len(reasons), 2)

    def test_grounding_and_refusal(self):
        result = {"grade": 2, "confidence": .285,
                  "probabilities": [.1, .272, .285, .15, .193],
                  "review_required": True, "review_reasons": ["Low confidence"],
                  "blur_check": {"grade": 1, "changed": True}}
        self.assertIn("28.5%", answer("Explain this result", result))
        self.assertIn("Grade 1", answer("What happened with blur?", result))
        self.assertIn("cannot diagnose", answer("Can you diagnose me?", result))


if __name__ == "__main__":
    unittest.main()
