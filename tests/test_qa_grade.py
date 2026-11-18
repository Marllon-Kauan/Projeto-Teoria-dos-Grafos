"""
Testes de QA da geração e edição da grade.

Cada teste roda num banco SQLite temporário criado a partir de
src/database/carga_de_dados.sql, então não depende de banco_projeto.db
nem altera o banco de desenvolvimento.

Rodar:  python -m pytest tests/test_qa_grade.py -v
"""

import random
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import repositorio as repo  # noqa: E402
from models.grafo import GrafoSemestre  # noqa: E402
from services.algorithm import (  # noqa: E402
    alocar_horarios,
    gerar_blocos_geminados,
    maior_sequencia_no_dia,
    ordenar_turmas,
)


# --------------------------------------------------------------- fixtures

@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / "banco_teste.db"
    with sqlite3.connect(db) as conn:
        conn.executescript((SRC / "database" / "carga_de_dados.sql").read_text(encoding="utf-8"))
    monkeypatch.setattr(repo, "DB_PATH", str(db))
    import app as appmod
    repo.garantir_esquema()
    appmod.app.config["TESTING"] = True
    return appmod.app.test_client()


def verificador():
    """Roda o src/verificar_regras.py no banco de teste e devolve os ERROS."""
    import contextlib
    import io
    import verificar_regras
    with contextlib.redirect_stdout(io.StringIO()):
        erros, _ = verificar_regras.main(2, db_path=repo.DB_PATH)
    return erros


def gerar(client):
    return client.post("/gerar", follow_redirects=True).get_data(as_text=True)


def violacoes():
    """Confere a grade salva contra TODAS as regras cadastradas no momento."""
    import app as appmod

    aulas = repo.aulas()
    turmas = {t["id"]: t for t in repo.turmas()}
    bloq = repo.bloqueados_por_periodo()
    restr = repo.restricoes_por_professor()
    limites = repo.limites_por_professor()
    erros = []

    por_horario = defaultdict(list)
    for a in aulas:
        por_horario[a["hor_id"]].append(a)
    for hor, grupo in por_horario.items():
        for i, x in enumerate(grupo):
            for y in grupo[i + 1:]:
                tx, ty = turmas[x["turma"]], turmas[y["turma"]]
                if tx["prof_id"] == ty["prof_id"]:
                    erros.append(("professor", tx["cod"], ty["cod"], hor))
                if (not tx.get("eletiva") and not ty.get("eletiva")
                        and tx["periodo"] is not None and tx["periodo"] == ty["periodo"]):
                    erros.append(("periodo", tx["cod"], ty["cod"], hor))
                if tx["dis_id"] == ty["dis_id"]:
                    erros.append(("disciplina", tx["cod"], hor))
                if x["sal_id"] is not None and x["sal_id"] == y["sal_id"]:
                    erros.append(("sala", tx["cod"], ty["cod"], hor))

    por_prof = defaultdict(list)
    for a in aulas:
        t = turmas[a["turma"]]
        if a["hor_id"] in restr.get(t["prof_id"], set()):
            erros.append(("restricao", t["cod"], a["hor_id"]))
        if not t.get("eletiva") and a["hor_id"] in bloq.get(t["periodo"], set()):
            erros.append(("bloqueio", t["cod"], a["hor_id"]))
        por_prof[t["prof_id"]].append((a["dia"], a["h"]))

    for prof, lim in limites.items():
        pos = por_prof.get(prof, [])
        if appmod.maior_sequencia(pos) > lim["seguidas"]:
            erros.append(("seguidas", prof))
        por_dia = defaultdict(int)
        for d, _ in pos:
            por_dia[d] += 1
        if por_dia and max(por_dia.values()) > lim["diarias"]:
            erros.append(("diarias", prof))
    return erros


# ------------------------------------------------------ algoritmo (unidade)

def _h(id_, dia, ordem, inicio, fim):
    return {"id": id_, "dia": dia, "ordem": ordem, "inicio": inicio, "fim": fim}


def test_blocos_geminados_so_juntam_horarios_consecutivos():
    horarios = [
        _h(1, 2, 0, "07:10", "08:00"),
        _h(2, 2, 1, "08:00", "08:50"),
        _h(3, 2, 2, "09:10", "10:00"),  # intervalo antes: não junta com o 2
        _h(4, 2, 3, "10:00", "10:50"),
    ]
    assert gerar_blocos_geminados(horarios) == [(1, 2), (3, 4)]


def test_maior_sequencia_no_dia():
    mapa = {1: (2, 0), 2: (2, 1), 3: (2, 2), 4: (3, 0), 5: (2, 4)}
    assert maior_sequencia_no_dia(mapa, [1, 2, 3, 5]) == 3
    assert maior_sequencia_no_dia(mapa, [1, 4, 5]) == 1
    assert maior_sequencia_no_dia(mapa, []) == 0


def _turma(tur_id, pro_id, aulas, dominio):
    return SimpleNamespace(
        tur_id=tur_id, pro_id=pro_id, aulas_semanais=aulas,
        dominio_horarios=set(dominio), horarios_alocados=[],
        max_seguidas=None, max_diarias=None,
    )


def test_ordenar_turmas_visita_todas_comecando_pelo_maior_grau():
    g = GrafoSemestre(1)
    for i in range(1, 6):
        g.add_vertice(_turma(i, i, 2, []))
    g.add_aresta(1, 2, ["x"]); g.add_aresta(2, 3, ["x"]); g.add_aresta(2, 4, ["x"])
    ordem = ordenar_turmas(g)
    assert ordem[0] == 2
    assert sorted(ordem) == [1, 2, 3, 4, 5]


def test_turmas_vizinhas_nunca_dividem_horario():
    horarios = [_h(i, 2 + i // 4, i % 4, None, None) for i in range(12)]
    g = GrafoSemestre(1)
    for i in range(1, 4):
        g.add_vertice(_turma(i, 100, 3, range(12)))
    g.add_aresta(1, 2, ["professor"]); g.add_aresta(1, 3, ["professor"]); g.add_aresta(2, 3, ["professor"])
    sem_horario = alocar_horarios(g, ordenar_turmas(g), horarios)
    assert sem_horario == []
    usados = [h for t in g.vertice_turmas.values() for h in t.horarios_alocados]
    assert len(usados) == len(set(usados)) == 9


def test_turma_sem_dominio_e_reportada_e_fica_sem_horario():
    horarios = [_h(i, 2, i, None, None) for i in range(4)]
    g = GrafoSemestre(1)
    g.add_vertice(_turma(1, 1, 2, []))
    sem_horario = alocar_horarios(g, [1], horarios)
    assert [t.tur_id for t in sem_horario] == [1]
    assert g.vertice_turmas[1].horarios_alocados == []


# ----------------------------------------------------- ponta a ponta (app)

def test_telas_principais_respondem(client):
    for rota in ["/", "/turmas", "/salas", "/restricoes", "/professores",
                 "/disciplinas", "/horarios", "/perfis", "/perfis/novo"]:
        assert client.get(rota).status_code == 200, rota


def test_geracao_com_dados_reais_respeita_todas_as_regras(client):
    assert "Grade gerada com sucesso" in gerar(client)
    assert violacoes() == []
    turmas = {t["id"]: t for t in repo.turmas()}
    aulas_por_turma = defaultdict(int)
    for a in repo.aulas():
        aulas_por_turma[a["turma"]] += 1
        assert a["sal_id"] is not None
    assert len(aulas_por_turma) == len(turmas)


@pytest.mark.parametrize("seed", range(10))
def test_geracao_com_restricoes_aleatorias(client, seed):
    rnd = random.Random(seed)
    profs = [p["id"] for p in repo.professores_detalhados()]
    hor_ids = sorted(repo.ids_do_algoritmo())
    for _ in range(rnd.randint(1, 12)):
        client.post("/restricoes/nova", data={
            "prof": rnd.choice(profs), "dia": rnd.choice(repo.DIAS),
            "h": rnd.choice([str(i) for i in range(len(repo.horarios()))] + ["todos"]),
            "motivo": "teste"})
    for p in rnd.sample(profs, 5):
        client.post("/preferencias/nova", data={
            "prof": p, "max_seg": rnd.choice("23"), "max_dia": rnd.choice("24")})
    for per in repo.PERIODOS_BLOQUEAVEIS:
        client.post("/restricoes/bloqueios", data={
            "periodo": per, "bloq": [str(h) for h in rnd.sample(hor_ids, 8)]})
    gerar(client)
    assert violacoes() == []
    assert verificador() == []


def test_mover_aula_nunca_aceita_movimento_invalido(client):
    gerar(client)
    rnd = random.Random(0)
    aulas = rnd.sample(repo.aulas(), 15)
    for aula in aulas:
        for dia in repo.DIAS:
            for h in range(len(repo.horarios())):
                r = client.post("/editar/mover", json={"aula_id": aula["id"], "dia": dia, "h": h})
                if r.get_json().get("ok"):
                    assert violacoes() == [], (aula["id"], dia, h)
                    repo.mover_aula(aula["id"], aula["hor_id"])


def test_mover_aula_com_dados_invalidos_retorna_400(client):
    gerar(client)
    for corpo in [{}, {"aula_id": 999999, "dia": "Seg", "h": 0},
                  {"aula_id": repo.aulas()[0]["id"], "dia": "Dom", "h": 0},
                  {"aula_id": repo.aulas()[0]["id"], "dia": "Seg", "h": 99}]:
        assert client.post("/editar/mover", json=corpo).status_code == 400


def test_geracao_parcial_nao_apresenta_grade_antiga_como_atual(client):
    gerar(client)
    todos = [str(h) for h in sorted(repo.ids_do_algoritmo())]
    client.post("/restricoes/bloqueios", data={"periodo": 1, "bloq": todos})
    assert "Não foi possível gerar a nova grade" in gerar(client)
    # Ou a grade é marcada como desatualizada, ou a grade exibida respeita as regras atuais.
    assert repo.grade_esta_desatualizada() or violacoes() == []


# ------------------------------------------------- verificar_regras.py

def test_verificador_aprova_grade_gerada(client):
    gerar(client)
    assert verificador() == []


def test_verificador_nao_aplica_bloqueio_de_um_periodo_em_outro(client):
    gerar(client)
    turmas = {t["id"]: t for t in repo.turmas()}
    usados_p1 = {a["hor_id"] for a in repo.aulas() if turmas[a["turma"]]["periodo"] == 1}
    hor = next(a["hor_id"] for a in repo.aulas()
               if turmas[a["turma"]]["periodo"] == 2 and a["hor_id"] not in usados_p1)
    client.post("/restricoes/bloqueios", data={"periodo": 1, "bloq": [str(hor)]})
    assert verificador() == []


def test_verificador_detecta_aula_em_horario_bloqueado(client):
    gerar(client)
    turmas = {t["id"]: t for t in repo.turmas()}
    aula = next(a for a in repo.aulas()
                if turmas[a["turma"]]["periodo"] == 1 and not turmas[a["turma"]].get("eletiva"))
    client.post("/restricoes/bloqueios", data={"periodo": 1, "bloq": [str(aula["hor_id"])]})
    assert any(e.startswith("[bloqueio]") for e in verificador())


def test_verificador_detecta_limite_diario_estourado(client):
    gerar(client)
    turmas = {t["id"]: t for t in repo.turmas()}
    por_prof_dia = defaultdict(int)
    for a in repo.aulas():
        por_prof_dia[(turmas[a["turma"]]["prof_id"], a["dia"])] += 1
    (prof, _dia), qtd = max(por_prof_dia.items(), key=lambda kv: kv[1])
    # cadastra um limite diário menor do que o professor já tem na grade salva
    repo.salvar_preferencia(prof, 3, qtd - 1)
    assert any(e.startswith("[diarias]") for e in verificador())
