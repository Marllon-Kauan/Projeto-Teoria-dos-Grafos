import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PerfilCurricularTemplateTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / "src" / "templates" / name).read_text(encoding="utf-8")

    def test_profile_templates_exist_and_expose_crud(self):
        listing = self.read("perfis.html")
        create = self.read("novo_perfil.html")
        edit = self.read("editar_perfil.html")
        view = self.read("visualizar_perfil.html")
        self.assertIn("listar_perfis", listing)
        self.assertIn("visualizar_perfil", listing)
        self.assertIn("editar_perfil", listing)
        self.assertIn("excluir_perfil", listing)
        self.assertIn('name="nome"', create)
        selector = self.read("_seletor_disciplinas.html")
        self.assertIn('_seletor_disciplinas.html', create)
        self.assertIn('_seletor_disciplinas.html', edit)
        self.assertIn('name="disciplinas"', selector)
        self.assertIn("Sem período específico", view)

    def test_profile_navigation_and_safe_application_notice(self):
        self.assertIn("carregar_perfil_turmas", self.read("index.html"))
        config_html = self.read("configurar_perfil_turmas.html")
        self.assertIn("aplicar_perfil_turmas", config_html)
        self.assertIn("Salvar configuração de turmas", config_html)

        confirm_html = self.read("confirmar_substituicao_turmas.html")
        self.assertIn("Confirmar substituição", confirm_html)
        self.assertIn("permanecerá preservada", confirm_html)

    def test_profile_selection_ui_is_shared_and_filterable(self):
        create = self.read("novo_perfil.html")
        edit = self.read("editar_perfil.html")
        for template in (create, edit):
            self.assertIn('_seletor_disciplinas.html', template)
        selector = self.read("_seletor_disciplinas.html")
        self.assertIn('class="seletor-disciplinas"', selector)
        self.assertIn('id="busca-disciplinas"', selector)
        self.assertIn('data-disciplina-item', selector)
        self.assertIn('data-contador-disciplinas', selector)
        self.assertIn('data-vazio-disciplinas', selector)
        self.assertIn('perfil_disciplinas.js', selector)
        script = self.read_js("perfil_disciplinas.js")
        self.assertIn("data-disciplina-item", script)
        self.assertIn("checked", script)
        self.assertIn("selectedCount", script)

    def read_js(self, name):
        return (ROOT / "src" / "static" / "js" / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
