import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import repositorio as repo


class HorariosValidationTests(unittest.TestCase):
    def test_accepts_consecutive_intervals(self):
        self.assertIsNone(repo.validar_faixa_horario("07:10", "08:00", []))
        self.assertIsNone(repo.validar_faixa_horario("08:00", "08:50", [(710, 800)]))

    def test_rejects_invalid_order_and_overlap(self):
        self.assertIsNotNone(repo.validar_faixa_horario("08:00", "07:10", []))
        self.assertIsNotNone(repo.validar_faixa_horario("07:10", "08:00", [(710, 800)]))
        self.assertIsNotNone(repo.validar_faixa_horario("07:30", "08:10", [(710, 800)]))


if __name__ == "__main__":
    unittest.main()
