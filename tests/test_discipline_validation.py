import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import repositorio as repo


class DisciplineValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.temp_dir.name) / "disciplinas.db"
        shutil.copyfile(ROOT / "src" / "banco_projeto.db", self.db_path)
        self.original_path = repo.DB_PATH
        self.original_semestre = repo.SEMESTRE_ID
        repo.DB_PATH = str(self.db_path)
        repo.SEMESTRE_ID = 2

    def tearDown(self):
        repo.DB_PATH = self.original_path
        repo.SEMESTRE_ID = self.original_semestre
        self.temp_dir.cleanup()

    def test_code_and_load_rules_are_validated(self):
        self.assertIn("4 letras", repo.criar_disciplina("AG", "Algoritmos", 1, 60, False))
        self.assertIn("múltipla", repo.criar_disciplina("CCMP0001", "Algoritmos", 1, 20, False))
        self.assertIn("período", repo.criar_disciplina("CCMP0001", "Algoritmos", None, 30, False))
        self.assertIsNone(repo.criar_disciplina("CCMP0001", "Algoritmos", None, 30, True))

    def test_affected_turmas_require_confirmation_and_remove_only_active_allocations(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO dis_disciplina (dis_id, dis_codigo, dis_nome, idper_periodo, dis_cargaHoraria, dis_eletiva) VALUES (900, 'ZZXY9990', 'Disciplina de teste', 1, 30, 0)")
            conn.execute("INSERT INTO tur_turma (tur_id, tur_codigo, idpro_professor, iddis_disciplina, idsem_semestre) VALUES (900, 'T1', 1, 900, 2)")
            conn.execute("INSERT INTO tur_turma (tur_id, tur_codigo, idpro_professor, iddis_disciplina, idsem_semestre) VALUES (901, 'T2', 1, 900, 1)")
            conn.execute("INSERT INTO alo_alocacaoHorarioSala (alo_id, idtur_turma, idsal_sala, idhor_horario) VALUES (900, 900, 1, 1)")
            conn.execute("INSERT INTO alo_alocacaoHorarioSala (alo_id, idtur_turma, idsal_sala, idhor_horario) VALUES (901, 901, 1, 1)")
            total_alocacoes = conn.execute("SELECT COUNT(*) FROM alo_alocacaoHorarioSala").fetchone()[0]

        afetadas = repo.turmas_com_alocacoes_disciplina(900)
        self.assertEqual(["T1"], [t["codigo"] for t in afetadas])
        erro, aviso = repo.atualizar_disciplina(900, "ZZXY9990", "Disciplina alterada", 1, 45, False)
        self.assertIn("confirmação", erro.lower())
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(total_alocacoes, conn.execute("SELECT COUNT(*) FROM alo_alocacaoHorarioSala").fetchone()[0])

        erro, aviso = repo.atualizar_disciplina(900, "ZZXY9990", "Disciplina alterada", 1, 45, False, confirmar=True)
        self.assertIsNone(erro)
        self.assertIsNotNone(aviso)
        with sqlite3.connect(self.db_path) as conn:
            ids = [r[0] for r in conn.execute("SELECT alo_id FROM alo_alocacaoHorarioSala ORDER BY alo_id")]
            self.assertNotIn(900, ids)
            self.assertIn(901, ids)

    def test_name_only_change_does_not_require_confirmation(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO dis_disciplina (dis_id, dis_codigo, dis_nome, idper_periodo, dis_cargaHoraria, dis_eletiva) VALUES (992, 'ZZXY9992', 'Nome antigo', 1, 30, 0)")
            conn.execute("INSERT INTO tur_turma (tur_id, tur_codigo, idpro_professor, iddis_disciplina, idsem_semestre) VALUES (992, 'T3', 1, 992, 2)")
            conn.execute("INSERT INTO alo_alocacaoHorarioSala (alo_id, idtur_turma, idsal_sala, idhor_horario) VALUES (992, 992, 1, 1)")
        erro, aviso = repo.atualizar_disciplina(992, "ZZXY9992", "Nome novo", 1, 30, False)
        self.assertIsNone(erro)
        self.assertIsNone(aviso)
