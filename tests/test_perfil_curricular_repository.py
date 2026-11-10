import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import repositorio as repo


class PerfilCurricularRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = Path(self.temp_dir.name) / "perfil.db"
        shutil.copyfile(ROOT / "src" / "banco_projeto.db", self.db)
        self.old = repo.DB_PATH
        repo.DB_PATH = str(self.db)
        repo.garantir_esquema()

    def tearDown(self):
        repo.DB_PATH = self.old
        self.temp_dir.cleanup()

    def test_create_rejects_empty_or_unknown_and_deduplicates(self):
        self.assertIn("nome", repo.criar_perfil("", [1]))
        self.assertIn("pelo menos uma disciplina", repo.criar_perfil("Vazio", []))
        self.assertIn("não existem", repo.criar_perfil("Inválido", [999999]))
        self.assertIsNone(repo.criar_perfil("Perfil teste", [1, 1]))
        perfil = repo.perfis()[-1]
        self.assertEqual(1, perfil["total_disciplinas"])

    def test_edit_and_delete_do_not_touch_turmas(self):
        self.assertIsNone(repo.criar_perfil("Perfil preservado", [1]))
        perfil = repo.perfis()[-1]
        with sqlite3.connect(self.db) as c:
            turmas_antes = c.execute("select count(*) from tur_turma").fetchone()[0]
        self.assertIsNone(repo.atualizar_perfil(perfil["id"], "Perfil alterado", [1, 2]))
        self.assertIsNone(repo.excluir_perfil(perfil["id"]))
        with sqlite3.connect(self.db) as c:
            self.assertEqual(turmas_antes, c.execute("select count(*) from tur_turma").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
