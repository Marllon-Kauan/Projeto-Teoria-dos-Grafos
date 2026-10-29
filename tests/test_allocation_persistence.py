import os
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.saver import alocar_salas


def _turma(tur_id, horarios):
    return SimpleNamespace(
        tur_id=tur_id,
        tur_codigo=tur_id,
        dis_nome="Disciplina",
        pro_nome="Professor",
        horarios_alocados=list(horarios),
    )


def _grafo(*turmas):
    return SimpleNamespace(vertice_turmas={turma.tur_id: turma for turma in turmas})


class AllocationPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(
                """
                CREATE TABLE sal_sala (
                    sal_id INTEGER PRIMARY KEY,
                    sal_bloco TEXT NOT NULL,
                    sal_numero INTEGER NOT NULL,
                    sal_status TEXT NOT NULL
                );
                CREATE TABLE tur_turma (
                    tur_id INTEGER PRIMARY KEY,
                    idsem_semestre INTEGER NOT NULL
                );
                CREATE TABLE alo_alocacaoHorarioSala (
                    alo_id INTEGER PRIMARY KEY,
                    idtur_turma INTEGER NOT NULL,
                    idsal_sala INTEGER,
                    idhor_horario INTEGER
                );
                """
            )
        finally:
            conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_room(self, room_id, status="Disponível"):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO sal_sala VALUES (?, ?, ?, ?)",
                (room_id, "A", room_id, status),
            )
            conn.commit()
        finally:
            conn.close()

    def add_class(self, class_id, semester=2):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("INSERT INTO tur_turma VALUES (?, ?)", (class_id, semester))
            conn.commit()
        finally:
            conn.close()

    def add_allocation(self, allocation_id, class_id, room_id, slot):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO alo_alocacaoHorarioSala VALUES (?, ?, ?, ?)",
                (allocation_id, class_id, room_id, slot),
            )
            conn.commit()
        finally:
            conn.close()

    def allocations(self):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(
                "SELECT alo_id, idtur_turma, idsal_sala, idhor_horario "
                "FROM alo_alocacaoHorarioSala ORDER BY alo_id"
            ).fetchall()
        finally:
            conn.close()

    def test_complete_generation_replaces_only_involved_classes(self):
        self.add_room(1)
        self.add_room(2)
        self.add_class(10)
        self.add_class(20)
        self.add_class(99, semester=1)
        self.add_allocation(5, 10, 1, 100)
        self.add_allocation(6, 99, 2, 200)

        failures = alocar_salas(
            self.db_path,
            _grafo(_turma(10, [1]), _turma(20, [2])),
            [10, 20],
        )

        self.assertEqual([], failures)
        self.assertEqual(
            [(6, 99, 2, 200), (7, 10, 1, 1), (8, 20, 1, 2)],
            self.allocations(),
        )

    def test_missing_room_preserves_previous_allocations(self):
        self.add_room(1)
        self.add_class(10)
        self.add_class(20)
        self.add_allocation(5, 10, 1, 100)

        failures = alocar_salas(
            self.db_path,
            _grafo(_turma(10, [1]), _turma(20, [1])),
            [10, 20],
        )

        self.assertEqual([20], [turma.tur_id for turma in failures])
        self.assertEqual([(5, 10, 1, 100)], self.allocations())

    def test_new_ids_do_not_collide_with_preserved_allocation(self):
        self.add_room(1)
        self.add_class(10)
        self.add_class(99, semester=1)
        self.add_allocation(40, 99, 1, 400)

        failures = alocar_salas(self.db_path, _grafo(_turma(10, [1])), [10])

        self.assertEqual([], failures)
        self.assertEqual([(40, 99, 1, 400), (41, 10, 1, 1)], self.allocations())

    def test_insert_exception_rolls_back_deletion(self):
        self.add_room(1)
        self.add_class(10)
        self.add_allocation(5, 10, 1, 100)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "CREATE TRIGGER fail_allocation_insert "
                "BEFORE INSERT ON alo_alocacaoHorarioSala "
                "BEGIN SELECT RAISE(ABORT, 'forced insert failure'); END;"
            )
            conn.commit()
        finally:
            conn.close()

        with self.assertRaises(sqlite3.IntegrityError):
            alocar_salas(self.db_path, _grafo(_turma(10, [1])), [10])

        self.assertEqual([(5, 10, 1, 100)], self.allocations())

    def test_generator_does_not_persist_rooms_when_schedule_has_failures(self):
        import importlib

        gerador = importlib.import_module("services.gerador")
        with patch.object(gerador, "construir_grafo") as build, \
                patch.object(gerador, "ordenar_turmas", return_value=[10]), \
                patch.object(gerador, "_obter_horarios_do_banco", return_value=[]), \
                patch.object(gerador, "alocar_horarios", return_value=[_turma(10, [])]), \
                patch.object(gerador, "alocar_salas") as allocate_rooms:
            graph = SimpleNamespace(vertice_turmas={10: _turma(10, [])})
            build.return_value = graph

            result = gerador.gerar_grade("unused.db", 2, {}, {}, {})

        allocate_rooms.assert_not_called()
        self.assertEqual(False, result["ok"])
        self.assertEqual(True, result["parcial"])
        self.assertEqual(1, len(result["turmas"]))

    def test_generator_success_keeps_existing_return_shape(self):
        import importlib

        gerador = importlib.import_module("services.gerador")
        graph = SimpleNamespace(vertice_turmas={10: _turma(10, [1])})
        with patch.object(gerador, "construir_grafo", return_value=graph), \
                patch.object(gerador, "ordenar_turmas", return_value=[10]), \
                patch.object(gerador, "_obter_horarios_do_banco", return_value=[]), \
                patch.object(gerador, "alocar_horarios", return_value=[]), \
                patch.object(gerador, "alocar_salas", return_value=[]):
            result = gerador.gerar_grade("unused.db", 2, {}, {}, {})

        self.assertEqual({"ok": True, "parcial": False, "turmas": []}, result)


if __name__ == "__main__":
    unittest.main()
