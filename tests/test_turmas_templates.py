import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TurmasTemplateTests(unittest.TestCase):
    def setUp(self):
        self.turmas = (ROOT / "src" / "templates" / "turmas.html").read_text(encoding="utf-8")
        self.edicao = (ROOT / "src" / "templates" / "editar_turma.html").read_text(encoding="utf-8")
        self.repositorio = (ROOT / "src" / "repositorio.py").read_text(encoding="utf-8")

    def test_cadastro_exige_disciplina_e_professor_explicitamente(self):
        self.assertIn('<option value="" selected disabled>Selecione a disciplina</option>', self.turmas)
        self.assertIn('<option value="" selected disabled>Selecione o professor</option>', self.turmas)

    def test_codigo_siga_de_duas_letras_e_mensagem_de_regeneracao(self):
        for template in (self.turmas, self.edicao):
            self.assertIn('pattern="[A-Za-z]{2}"', template)
            self.assertIn('maxlength="2"', template)
        self.assertIn("Ao trocar a disciplina ou o professor", self.edicao)

    def test_edicao_remove_alocacoes_para_disciplina_ou_professor(self):
        self.assertIn("if mudou_disciplina or mudou_professor:", self.repositorio)
        self.assertIn('DELETE FROM alo_alocacaoHorarioSala WHERE idtur_turma = ?', self.repositorio)

    def test_edicao_de_sala_preserva_alocacoes(self):
        self.assertIn("if sala_id is not None and aulas_turma and not (mudou_disciplina or mudou_professor):", self.repositorio)
        self.assertIn('UPDATE alo_alocacaoHorarioSala SET idsal_sala = ? WHERE idtur_turma = ?', self.repositorio)


if __name__ == "__main__":
    unittest.main()
