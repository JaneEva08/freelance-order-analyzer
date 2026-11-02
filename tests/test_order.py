import copy
import unittest
from analyze_order import validate


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.source = "Система должна исключать дублирование клиентов."
        self.data = {
            "title": "CRM", "goal": "Работа с клиентами",
            "budget": {"value": None, "note": "Не указано"},
            "deadline": {"value": None, "note": "Не указано"},
            "acceptance_criteria": [],
            "requirements": [{"id": "REQ-001", "description": "Исключать дубли",
                              "status": "required", "evidence": self.source}],
            "clarifications": [{"requirement_id": "REQ-001", "gap": "Нет правил",
                                "question": "По каким данным определять дубль?"}]}

    def test_valid(self):
        self.assertIs(validate(self.data, self.source), self.data)

    def test_invented_quote_rejected(self):
        self.data["requirements"][0]["evidence"] = "Срок — неделя"
        with self.assertRaises(ValueError):
            validate(self.data, self.source)

    def test_dangling_question_rejected(self):
        self.data["clarifications"][0]["requirement_id"] = "REQ-999"
        with self.assertRaises(ValueError):
            validate(self.data, self.source)

    def test_duplicate_ids_rejected(self):
        self.data["requirements"].append(copy.deepcopy(self.data["requirements"][0]))
        with self.assertRaises(ValueError):
            validate(self.data, self.source)


if __name__ == "__main__":
    unittest.main()
