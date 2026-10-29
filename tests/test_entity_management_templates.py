import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EntityManagementTemplateTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / "src" / "templates" / name).read_text(encoding="utf-8")

    def test_professor_templates_expose_required_operations(self):
        listing = self.read("professores.html")
        editing = self.read("editar_professor.html")
        self.assertIn('name="nome"', listing)
        self.assertIn('name="email"', listing)
        self.assertIn("url_for('editar_professor'", listing)
        self.assertIn("url_for('excluir_professor'", listing)
        self.assertIn('name="nome"', editing)
        self.assertIn('name="email"', editing)
        self.assertIn("Salvar alterações", editing)
        self.assertIn("Cancelar", editing)

    def test_discipline_templates_expose_rules_and_operations(self):
        listing = self.read("disciplinas.html")
        editing = self.read("editar_disciplina.html")
        for field in ('codigo', 'nome', 'periodo', 'carga', 'eletiva'):
            self.assertIn(f'name="{field}"', listing)
            self.assertIn(f'name="{field}"', editing)
        self.assertIn("Sem período específico", listing)
        self.assertIn("url_for('editar_disciplina'", listing)
        self.assertIn("url_for('excluir_disciplina'", listing)
        self.assertIn("Salvar alterações", editing)
        self.assertIn("Cancelar", editing)

    def test_navigation_exposes_both_new_pages(self):
        for name in ("index.html", "turmas.html", "restricoes.html", "salas.html"):
            template = self.read(name)
            self.assertIn("url_for('listar_professores')", template)
            self.assertIn("url_for('listar_disciplinas')", template)


if __name__ == "__main__":
    unittest.main()
