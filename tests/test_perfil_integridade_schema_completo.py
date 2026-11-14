import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import repositorio as repo


class PerfilIntegridadeSchemaCompletoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "schema-completo.db"
        self.old_db = repo.DB_PATH
        repo.DB_PATH = str(self.db_path)
        db = sqlite3.connect(self.db_path)
        try:
            db.execute("PRAGMA foreign_keys = ON")
            db.executescript((ROOT / "src" / "database" / "carga_de_dados.sql").read_text(encoding="utf-8"))
            db.commit()
        finally:
            db.close()
        repo.garantir_esquema()
        db = sqlite3.connect(self.db_path)
        try:
            db.execute("UPDATE alo_alocacaoHorarioSala SET idsal_sala = 1 WHERE idtur_turma = 1 AND idhor_horario = 24")
            db.execute("INSERT INTO per_perfil (prf_id, prf_nome) VALUES (1, 'Perfil completo')")
            db.executemany("INSERT INTO pdis_perfil_disciplina VALUES (1, ?)", [(1,), (2,)])
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        repo.DB_PATH = self.old_db
        self.tmp.cleanup()

    def _read(self, sql):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        try:
            return db.execute(sql).fetchall()
        finally:
            db.close()

    def test_declared_foreign_keys_and_clean_check_before_and_after(self):
        fk_tables = {
            "dis_disciplina", "tur_turma", "alo_alocacaoHorarioSala",
            "pdis_perfil_disciplina"
        }
        declared = {table: self._read(f"PRAGMA foreign_key_list({table})") for table in fk_tables}
        self.assertTrue(declared["tur_turma"])
        self.assertTrue(declared["alo_alocacaoHorarioSala"])
        self.assertTrue(declared["pdis_perfil_disciplina"])

        db = sqlite3.connect(self.db_path)
        try:
            db.execute("PRAGMA foreign_keys = ON")
            self.assertEqual(1, db.execute("PRAGMA foreign_keys").fetchone()[0])
            self.assertEqual([], db.execute("PRAGMA foreign_key_check").fetchall())
        finally:
            db.close()

        config = [
            {"dis_id": 1, "codigo": "MD", "prof_id": 1},
            {"dis_id": 2, "codigo": "TG", "prof_id": 2},
        ]
        active_allocations = self._read(
            "SELECT COUNT(*) FROM alo_alocacaoHorarioSala A JOIN tur_turma T ON T.tur_id = A.idtur_turma WHERE T.idsem_semestre = 2"
        )[0][0]
        self.assertEqual("CONFIRMACAO_NECESSARIA", repo.aplicar_perfil_turmas(1, config))
        self.assertIsNone(repo.aplicar_perfil_turmas(1, config, confirmar=True))

        db = sqlite3.connect(self.db_path)
        try:
            db.execute("PRAGMA foreign_keys = ON")
            self.assertEqual([], db.execute("PRAGMA foreign_key_check").fetchall())
            self.assertEqual(active_allocations, db.execute("SELECT COUNT(*) FROM grd_snapshot_aula WHERE idsem_semestre = 2").fetchone()[0])
            self.assertEqual(1, db.execute("SELECT config_pendente FROM grd_estado_semestre WHERE idsem_semestre = 2").fetchone()[0])
            self.assertEqual(0, db.execute("SELECT COUNT(*) FROM tur_turma WHERE idsem_semestre = 1").fetchone()[0])
        finally:
            db.close()

    def test_production_connections_do_not_enable_foreign_keys(self):
        with repo.conexao() as db:
            self.assertEqual(0, db.execute("PRAGMA foreign_keys").fetchone()[0])

    def test_snapshot_preserves_allocation_without_room(self):
        db = sqlite3.connect(self.db_path)
        try:
            db.execute("UPDATE alo_alocacaoHorarioSala SET idsal_sala = NULL WHERE idtur_turma = 1")
            before = db.execute(
                "SELECT COUNT(*) FROM alo_alocacaoHorarioSala A JOIN tur_turma T ON T.tur_id = A.idtur_turma WHERE T.idsem_semestre = 2"
            ).fetchone()[0]
            db.commit()
        finally:
            db.close()

        config = [
            {"dis_id": 1, "codigo": "MD", "prof_id": 1},
            {"dis_id": 2, "codigo": "TG", "prof_id": 2},
        ]
        self.assertIsNone(repo.aplicar_perfil_turmas(1, config, confirmar=True))
        snapshot_count = self._read(
            "SELECT COUNT(*) FROM grd_snapshot_aula WHERE idsem_semestre = 2"
        )[0][0]
        self.assertGreater(before, 0)
        self.assertEqual(before, snapshot_count)
        self.assertEqual([(before,)], [tuple(r) for r in self._read(
            "SELECT COUNT(*) FROM grd_snapshot_aula WHERE idsem_semestre = 2 AND sal_id IS NULL"
        )])

    def test_snapshot_schema_migration_preserves_rows_and_is_idempotent(self):
        db = sqlite3.connect(self.db_path)
        try:
            db.execute("DROP TABLE grd_snapshot_aula")
            db.execute("""
                CREATE TABLE grd_snapshot_aula (
                    snp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idsem_semestre INT NOT NULL, tur_id_orig INT NOT NULL,
                    tur_codigo TEXT NOT NULL, dis_id INT NOT NULL,
                    dis_codigo TEXT NOT NULL, dis_nome TEXT NOT NULL,
                    idper_periodo INT, dis_eletiva INT NOT NULL DEFAULT 0,
                    pro_id INT NOT NULL, pro_nome TEXT NOT NULL,
                    sal_id INT NOT NULL, sal_bloco TEXT NOT NULL,
                    sal_numero INT NOT NULL, idhor_horario INT NOT NULL
                )
            """)
            db.execute("""INSERT INTO grd_snapshot_aula
                (idsem_semestre, tur_id_orig, tur_codigo, dis_id, dis_codigo,
                 dis_nome, pro_id, pro_nome, sal_id, sal_bloco, sal_numero, idhor_horario)
                VALUES (2, 77, 'AA', 1, 'CCMP0001', 'Grafos', 1, 'Prof', 1, 'I', 1, 24)
            """)
            db.commit()
        finally:
            db.close()

        repo.garantir_esquema()
        self.assertEqual([(77, 1, 'I', 1)], [tuple(r) for r in self._read(
            "SELECT tur_id_orig, sal_id, sal_bloco, sal_numero FROM grd_snapshot_aula")])
        repo.garantir_esquema()
        self.assertEqual(1, self._read("SELECT COUNT(*) FROM grd_snapshot_aula")[0][0])
        columns = {r[1]: r[3] for r in self._read("PRAGMA table_info(grd_snapshot_aula)")}
        self.assertEqual(0, columns["sal_id"])
        self.assertEqual(0, columns["sal_bloco"])
        self.assertEqual(0, columns["sal_numero"])


if __name__ == "__main__":
    unittest.main()
