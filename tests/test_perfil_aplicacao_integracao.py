import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import repositorio as repo


class PerfilAplicacaoIntegracaoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = repo.DB_PATH
        repo.DB_PATH = str(Path(self.tmp.name) / "perfil-integracao.db")
        db = sqlite3.connect(repo.DB_PATH)
        try:
            db.executescript("""
                CREATE TABLE per_perfil (prf_id INTEGER PRIMARY KEY, prf_nome TEXT NOT NULL);
                CREATE TABLE pdis_perfil_disciplina (idprf_perfil INTEGER, iddis_disciplina INTEGER,
                    PRIMARY KEY (idprf_perfil, iddis_disciplina));
                CREATE TABLE dis_disciplina (dis_id INTEGER PRIMARY KEY, dis_codigo TEXT,
                    dis_nome TEXT, idper_periodo INTEGER, dis_eletiva INTEGER DEFAULT 0,
                    dis_cargaHoraria INTEGER DEFAULT 60);
                CREATE TABLE pro_professor (pro_id INTEGER PRIMARY KEY, pro_nome TEXT, pro_email TEXT);
                CREATE TABLE tur_turma (tur_id INTEGER PRIMARY KEY, tur_codigo TEXT,
                    idpro_professor INTEGER, iddis_disciplina INTEGER, idsem_semestre INTEGER);
                CREATE TABLE sal_sala (sal_id INTEGER PRIMARY KEY, sal_bloco TEXT, sal_numero INTEGER);
                CREATE TABLE alo_alocacaoHorarioSala (alo_id INTEGER PRIMARY KEY, idtur_turma INTEGER,
                    idsal_sala INTEGER, idhor_horario INTEGER);
                CREATE TABLE grd_snapshot_aula (snp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idsem_semestre INT, tur_id_orig INT, tur_codigo TEXT, dis_id INT,
                    dis_codigo TEXT, dis_nome TEXT, idper_periodo INT, dis_eletiva INT,
                    pro_id INT, pro_nome TEXT, sal_id INT, sal_bloco TEXT,
                    sal_numero INT, idhor_horario INT);
                CREATE TABLE grd_estado_semestre (idsem_semestre INTEGER PRIMARY KEY, config_pendente INT NOT NULL DEFAULT 0);
                INSERT INTO dis_disciplina VALUES (1, 'CCMP0001', 'Grafos', 1, 0, 60);
                INSERT INTO dis_disciplina VALUES (2, 'CCMP0002', 'Algoritmos', 2, 0, 60);
                INSERT INTO pro_professor VALUES (1, 'Prof. Um', 'um@example.com');
                INSERT INTO pro_professor VALUES (2, 'Prof. Dois', 'dois@example.com');
                INSERT INTO sal_sala VALUES (1, 'A', 101);
                INSERT INTO per_perfil VALUES (1, 'Perfil novo');
                INSERT INTO pdis_perfil_disciplina VALUES (1, 1);
                INSERT INTO pdis_perfil_disciplina VALUES (1, 2);
                INSERT INTO tur_turma VALUES (10, 'AA', 1, 1, 2);
                INSERT INTO tur_turma VALUES (20, 'ZZ', 2, 2, 3);
                INSERT INTO alo_alocacaoHorarioSala VALUES (100, 10, 1, 7);
            """)
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        repo.DB_PATH = self.old_db
        self.tmp.cleanup()

    def _config(self):
        return [
            {"dis_id": 1, "codigo": "MD", "prof_id": 1},
            {"dis_id": 2, "codigo": "TG", "prof_id": 2},
            {"dis_id": 2, "codigo": "MA", "prof_id": 1},
        ]

    def _query(self, sql):
        db = sqlite3.connect(repo.DB_PATH)
        try:
            return db.execute(sql).fetchall()
        finally:
            db.close()

    def test_requires_confirmation_and_replaces_only_active_semester(self):
        self.assertEqual("CONFIRMACAO_NECESSARIA", repo.aplicar_perfil_turmas(1, self._config()))
        self.assertEqual([(10, "AA"), (20, "ZZ")], self._query(
            "SELECT tur_id, tur_codigo FROM tur_turma ORDER BY tur_id"))

        self.assertIsNone(repo.aplicar_perfil_turmas(1, self._config(), confirmar=True))
        self.assertEqual([("ZZ", 3), ("MD", 2), ("TG", 2), ("MA", 2)], self._query(
            "SELECT tur_codigo, idsem_semestre FROM tur_turma ORDER BY tur_id"))
        self.assertEqual([(1,)], self._query("SELECT COUNT(*) FROM grd_snapshot_aula"))
        self.assertEqual([(1,)], self._query(
            "SELECT config_pendente FROM grd_estado_semestre WHERE idsem_semestre = 2"))
        self.assertEqual([(20, "ZZ", 3)], self._query(
            "SELECT tur_id, tur_codigo, idsem_semestre FROM tur_turma WHERE idsem_semestre = 3"))

    def test_validation_and_cancel_do_not_modify_database(self):
        before = self._query("SELECT COUNT(*) FROM tur_turma")[0][0]
        self.assertIn("exatamente 2 letras", repo.aplicar_perfil_turmas(1, [
            {"dis_id": 1, "codigo": "ABC", "prof_id": 1},
            {"dis_id": 2, "codigo": "TG", "prof_id": 2},
        ]))
        self.assertIn("duplicado", repo.aplicar_perfil_turmas(1, [
            {"dis_id": 1, "codigo": "MD", "prof_id": 1},
            {"dis_id": 2, "codigo": "MD", "prof_id": 2},
        ]))
        self.assertIn("professor", repo.aplicar_perfil_turmas(1, [
            {"dis_id": 1, "codigo": "MD", "prof_id": ""},
            {"dis_id": 2, "codigo": "TG", "prof_id": 2},
        ]))
        self.assertEqual(before, self._query("SELECT COUNT(*) FROM tur_turma")[0][0])

    def test_insert_failure_rolls_back_deletion_and_snapshot(self):
        db = sqlite3.connect(repo.DB_PATH)
        try:
            db.execute("CREATE TRIGGER fail_new_turma BEFORE INSERT ON tur_turma BEGIN SELECT RAISE(ABORT, 'forced failure'); END")
            db.commit()
        finally:
            db.close()
        with self.assertRaises(sqlite3.IntegrityError):
            repo.aplicar_perfil_turmas(1, self._config(), confirmar=True)
        self.assertEqual([(10, "AA"), (20, "ZZ")], self._query(
            "SELECT tur_id, tur_codigo FROM tur_turma ORDER BY tur_id"))
        self.assertEqual([(0,)], self._query("SELECT COUNT(*) FROM grd_snapshot_aula"))


if __name__ == "__main__":
    unittest.main()
