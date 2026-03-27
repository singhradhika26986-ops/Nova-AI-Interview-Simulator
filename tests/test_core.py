import unittest
from pathlib import Path

import auth
import database
from answer_evaluator import evaluate_answer
from report_export import build_recommendation, generate_report_text


class AuthTests(unittest.TestCase):
    def test_password_hash_and_verify(self):
        hashed = auth.hash_password("secret123")
        self.assertTrue(auth.verify_password("secret123", hashed))
        self.assertFalse(auth.verify_password("wrongpass", hashed))


class EvaluatorTests(unittest.TestCase):
    def test_local_evaluation_returns_expected_shape(self):
        result = evaluate_answer(
            answer="A list is an ordered mutable collection used to store multiple items.",
            question="What is a list in Python?",
            expected_answer="A list is an ordered and mutable collection in Python used to store multiple items that may change over time.",
            topic="Python",
            keywords=["ordered", "mutable", "collection", "multiple items"],
        )
        self.assertIn("overall_score", result)
        self.assertIn("rubric", result)
        self.assertGreaterEqual(result["overall_score"], 0)


class ReportTests(unittest.TestCase):
    def test_report_text_and_recommendation(self):
        report_text, average_score, recommendation = generate_report_text(
            "Test User",
            "Python",
            [
                {
                    "question": "What is a list in Python?",
                    "overall_score": 8.0,
                    "verdict": "Strong answer",
                    "strengths": ["Clear explanation"],
                    "improvements": ["Add one example"],
                    "summary": "Good answer.",
                }
            ],
        )
        self.assertIn("Test User", report_text)
        self.assertEqual(average_score, 8.0)
        self.assertEqual(recommendation, build_recommendation(8.0))


class DatabaseTests(unittest.TestCase):
    def test_database_initialization_and_user_creation(self):
        original_db_path = database.DB_PATH
        test_db_path = Path(__file__).resolve().parent / "test_project.db"
        if test_db_path.exists():
            test_db_path.unlink()
        try:
            database.DB_PATH = test_db_path
            database.init_db()
            user_id = database.create_user("Test User", "test@example.com", "hash-value")
            user = database.get_user_by_id(user_id)
            self.assertEqual(user["email"], "test@example.com")
            database.upsert_practice_progress(user_id, "Python", "q1", is_bookmarked=1, is_completed=1)
            progress = database.get_practice_progress(user_id)
            self.assertEqual(len(progress), 1)
            self.assertEqual(progress[0]["is_bookmarked"], 1)
        finally:
            database.DB_PATH = original_db_path
            if test_db_path.exists():
                try:
                    test_db_path.unlink()
                except PermissionError:
                    pass


if __name__ == "__main__":
    unittest.main()
