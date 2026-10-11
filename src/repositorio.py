# -*- coding: utf-8 -*-
"""
Camada de acesso ao banco para o front (app.py).

Substitui o antigo dados.py (listas em memoria). Cada funcao le o SQLite e
devolve dicionarios no mesmo formato que as telas ja usavam, entao os templates
mudam pouco.
"""

import os
import sqlite3
from contextlib import contextmanager
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "banco_projeto.db")

SEMESTRE_ID = 2          # mesmo valor que o main.py usa
ANO = 2026               # o banco guarda so 1 ou 2; o ano e so o rotulo da tela

DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
DIAS_LONGO = {
    "Seg": "Segunda", "Ter": "Terca", "Qua": "Quarta",
    "Qui": "Quinta", "Sex": "Sexta", "Sab": "Sabado",
}
# hor_diaSemana no banco: 2 = segunda ... 7 = sabado
DIA_POR_NUM = {2: "Seg", 3: "Ter", 4: "Qua", 5: "Qui", 6: "Sex", 7: "Sab"}

# O banco do back tem segunda a sexta com 6 horarios (A a F). O front tambem
# mostra o 7o horario (12:10-13:00) e o sabado. Se o banco ainda nao tiver essas
# linhas, garantir_esquema() as cria com ids novos, sem mexer nos existentes.
FAIXAS = [(710, 800), (800, 850), (850, 940), (940, 1030), (1030, 1120), (1120, 1210), (1210, 1300)]
SLOTS = "ABCDEFG"
# (hor_diaSemana, hor_slot) que o front precisa ter.
HORARIOS_DO_FRONT = [(d, SLOTS[i]) for d in range(2, 8) for i in range(7)]

PERIODOS = list(range(1, 11))
PERIODOS_BLOQUEAVEIS = (1, 2, 3, 4)   # mesma regra do builder.py


# ---------------------------------------------------------------- conexao

@contextmanager
def conexao():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def garantir_esquema():
    """
    Confere que o banco foi criado (setup_db.py) e cria as duas tabelas novas
    usadas pelo front: restricoes de professor e horarios bloqueados.
    """
    with conexao() as c:
        existentes = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "hor_horario" not in existentes:
            raise RuntimeError(
                "Banco sem tabelas em %s. Rode primeiro: python setup_db.py" % DB_PATH)
        for dia, slot in HORARIOS_DO_FRONT:
            if not c.execute("SELECT 1 FROM hor_horario WHERE hor_diaSemana = ? AND hor_slot = ?",
                             (dia, slot)).fetchone():
                novo = (c.execute("SELECT MAX(hor_id) FROM hor_horario").fetchone()[0] or 0) + 1
                ini, fim = FAIXAS[SLOTS.index(slot)]
                c.execute(
                    "INSERT INTO hor_horario (hor_id, hor_diaSemana, hor_slot, hor_horaInicio, hor_horaFim) "
                    "VALUES (?, ?, ?, ?, ?)", (novo, dia, slot, ini, fim))
        c.execute("""
            CREATE TABLE IF NOT EXISTS res_restricao (
                res_id INTEGER PRIMARY KEY AUTOINCREMENT,
                idpro_professor INT NOT NULL,
                idhor_horario INT NOT NULL,
                res_motivo VARCHAR(200)
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS pre_preferencia (
                idpro_professor INT PRIMARY KEY,
                pre_maxSeguidas INT NOT NULL
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS blq_bloqueio (
                idhor_horario INT PRIMARY KEY
            )""")


# ---------------------------------------------------------------- horarios

def _fmt_hora(valor):
    s = str(valor).zfill(4)
    return "%s:%s" % (s[:2], s[2:])


@lru_cache(maxsize=1)
def _mapa_horarios():
    with conexao() as c:
        linhas = c.execute(
            "SELECT hor_id, hor_diaSemana, hor_slot, hor_horaInicio, hor_horaFim "
            "FROM hor_horario ORDER BY hor_id").fetchall()
    por_id, por_dia_h, faixas = {}, {}, {}
    for r in linhas:
        dia = DIA_POR_NUM.get(r["hor_diaSemana"])
        if dia is None:
            continue
        h = ord(r["hor_slot"]) - ord("A")          # A=0, B=1, ... F=5
        por_id[r["hor_id"]] = (dia, h)
        por_dia_h[(dia, h)] = r["hor_id"]
        faixas[h] = "%s - %s" % (_fmt_hora(r["hor_horaInicio"]), _fmt_hora(r["hor_horaFim"]))
    return por_id, por_dia_h, [faixas[i] for i in sorted(faixas)]


def horarios():
    """Lista de faixas ('07:10 - 08:00'), indice = slot A..F."""
    return _mapa_horarios()[2]


def hor_id(dia, h):
    return _mapa_horarios()[1].get((dia, h))


def ids_do_algoritmo():
    """Horarios que o algoritmo do back usa: segunda a sexta, slots A a F."""
    return {i for i, (dia, h) in _mapa_horarios()[0].items() if dia != "Sab" and h < 6}


def ids_por_dia_h():
    return _mapa_horarios()[1]


def dia_h(hor_id_):
    return _mapa_horarios()[0].get(hor_id_)


# ---------------------------------------------------------------- consultas

def semestre():
    return "%d.%d" % (ANO, SEMESTRE_ID)


def professores():
    with conexao() as c:
        return [r[0] for r in c.execute("SELECT pro_nome FROM pro_professor ORDER BY pro_nome")]


def _prof_id(nome):
    with conexao() as c:
        r = c.execute("SELECT pro_id FROM pro_professor WHERE pro_nome = ?", (nome,)).fetchone()
    return r[0] if r else None


def disciplinas():
    """{codigo: {nome, cor, id, periodo}} - cor 1..4 so para colorir a grade."""
    with conexao() as c:
        linhas = c.execute(
            "SELECT dis_id, dis_codigo, dis_nome, idper_periodo FROM dis_disciplina "
            "ORDER BY dis_nome").fetchall()
    return {
        r["dis_codigo"]: {
            "id": r["dis_id"], "nome": r["dis_nome"],
            "periodo": r["idper_periodo"], "cor": (r["dis_id"] % 4) + 1,
        } for r in linhas
    }


def turmas():
    with conexao() as c:
        linhas = c.execute("""
            SELECT TUR.tur_id, TUR.tur_codigo, DIS.dis_codigo, DIS.dis_id,
                   DIS.idper_periodo, PRO.pro_nome, PRO.pro_id
            FROM tur_turma TUR
            JOIN dis_disciplina DIS ON DIS.dis_id = TUR.iddis_disciplina
            JOIN pro_professor PRO ON PRO.pro_id = TUR.idpro_professor
            WHERE TUR.idsem_semestre = ?
            ORDER BY TUR.tur_id""", (SEMESTRE_ID,)).fetchall()
        salas = {}
        for r in c.execute("""
            SELECT DISTINCT ALO.idtur_turma, SAL.sal_bloco, SAL.sal_numero
            FROM alo_alocacaoHorarioSala ALO
            JOIN sal_sala SAL ON SAL.sal_id = ALO.idsal_sala
            ORDER BY SAL.sal_bloco, SAL.sal_numero"""):
            salas.setdefault(r[0], []).append("%s-%s" % (r[1], r[2]))
    return [{
        "id": r["tur_id"], "cod": r["dis_codigo"], "turma": str(r["tur_codigo"]),
        "prof": r["pro_nome"], "prof_id": r["pro_id"], "dis_id": r["dis_id"],
        "periodo": r["idper_periodo"],
        "sala": ", ".join(salas.get(r["tur_id"], [])),
    } for r in linhas]


def buscar_turma(turma_id):
    return next((t for t in turmas() if t["id"] == turma_id), None)


def aulas():
    with conexao() as c:
        linhas = c.execute("""
            SELECT ALO.alo_id, ALO.idtur_turma, ALO.idhor_horario,
                   SAL.sal_id, SAL.sal_bloco, SAL.sal_numero
            FROM alo_alocacaoHorarioSala ALO
            JOIN tur_turma TUR ON TUR.tur_id = ALO.idtur_turma
            JOIN sal_sala SAL ON SAL.sal_id = ALO.idsal_sala
            WHERE TUR.idsem_semestre = ?
            ORDER BY ALO.alo_id""", (SEMESTRE_ID,)).fetchall()
    resultado = []
    for r in linhas:
        pos = dia_h(r["idhor_horario"])
        if pos is None:
            continue
        resultado.append({
            "id": r["alo_id"], "turma": r["idtur_turma"],
            "dia": pos[0], "h": pos[1], "hor_id": r["idhor_horario"],
            "sal_id": r["sal_id"],
            "sala": "%s-%s" % (r["sal_bloco"], r["sal_numero"]),
        })
    return resultado


def restricoes():
    with conexao() as c:
        linhas = c.execute("""
            SELECT R.res_id, R.idpro_professor, R.idhor_horario, R.res_motivo, P.pro_nome
            FROM res_restricao R
            JOIN pro_professor P ON P.pro_id = R.idpro_professor
            ORDER BY P.pro_nome, R.idhor_horario""").fetchall()
    resultado = []
    for r in linhas:
        pos = dia_h(r["idhor_horario"])
        if pos is None:
            continue
        resultado.append({
            "id": r["res_id"], "prof": r["pro_nome"], "prof_id": r["idpro_professor"],
            "dia": pos[0], "h": pos[1], "hor_id": r["idhor_horario"],
            "motivo": r["res_motivo"],
        })
    return resultado


def restricoes_por_professor():
    """{pro_id: {hor_id, ...}} no formato que o builder.py recebe."""
    mapa = {}
    for r in restricoes():
        mapa.setdefault(r["prof_id"], set()).add(r["hor_id"])
    return mapa


def preferencias():
    """Limite de aulas seguidas no mesmo dia, por professor."""
    with conexao() as c:
        linhas = c.execute("""
            SELECT P.pro_id, P.pro_nome, F.pre_maxSeguidas
            FROM pre_preferencia F JOIN pro_professor P ON P.pro_id = F.idpro_professor
            ORDER BY P.pro_nome""").fetchall()
    return [{"prof_id": r[0], "prof": r[1], "max": r[2]} for r in linhas]


def max_seguidas_por_professor():
    """{pro_id: n} no formato que o builder.py recebe."""
    return {p["prof_id"]: p["max"] for p in preferencias()}


def bloqueados():
    with conexao() as c:
        return {r[0] for r in c.execute("SELECT idhor_horario FROM blq_bloqueio")}


# ---------------------------------------------------------------- escrita

def criar_turma(cod_disciplina, codigo_turma, prof_nome):
    """Retorna None se cadastrou, ou a mensagem de erro."""
    dis = disciplinas().get(cod_disciplina)
    pro_id = _prof_id(prof_nome)
    if dis is None or pro_id is None:
        return "Disciplina ou professor invalido."
    with conexao() as c:
        if c.execute("SELECT 1 FROM tur_turma WHERE tur_codigo = ? AND idsem_semestre = ?",
                     (codigo_turma, SEMESTRE_ID)).fetchone():
            return "Ja existe uma turma com o codigo %s neste semestre." % codigo_turma
        novo = (c.execute("SELECT MAX(tur_id) FROM tur_turma").fetchone()[0] or 0) + 1
        c.execute(
            "INSERT INTO tur_turma (tur_id, tur_codigo, idpro_professor, iddis_disciplina, idsem_semestre) "
            "VALUES (?, ?, ?, ?, ?)", (novo, codigo_turma, pro_id, dis["id"], SEMESTRE_ID))
    return None


def excluir_turma(turma_id):
    with conexao() as c:
        c.execute("DELETE FROM alo_alocacaoHorarioSala WHERE idtur_turma = ?", (turma_id,))
        c.execute("DELETE FROM tur_turma WHERE tur_id = ?", (turma_id,))


def criar_restricao(prof_nome, dia, h, motivo):
    pro_id = _prof_id(prof_nome)
    hid = hor_id(dia, h)
    if pro_id is None or hid is None:
        return False
    with conexao() as c:
        c.execute(
            "INSERT INTO res_restricao (idpro_professor, idhor_horario, res_motivo) VALUES (?, ?, ?)",
            (pro_id, hid, motivo))
    return True


def excluir_restricao(restricao_id):
    with conexao() as c:
        c.execute("DELETE FROM res_restricao WHERE res_id = ?", (restricao_id,))


def salvar_preferencia(prof_nome, maximo):
    pro_id = _prof_id(prof_nome)
    if pro_id is None:
        return False
    with conexao() as c:
        c.execute("INSERT OR REPLACE INTO pre_preferencia (idpro_professor, pre_maxSeguidas) VALUES (?, ?)",
                  (pro_id, maximo))
    return True


def excluir_preferencia(pro_id):
    with conexao() as c:
        c.execute("DELETE FROM pre_preferencia WHERE idpro_professor = ?", (pro_id,))


def salvar_bloqueados(ids):
    validos = set(_mapa_horarios()[0].keys())
    ids = {i for i in ids if i in validos}
    with conexao() as c:
        c.execute("DELETE FROM blq_bloqueio")
        c.executemany("INSERT INTO blq_bloqueio (idhor_horario) VALUES (?)", [(i,) for i in ids])
    return ids


def mover_aula(aula_id, novo_hor_id):
    with conexao() as c:
        c.execute("UPDATE alo_alocacaoHorarioSala SET idhor_horario = ? WHERE alo_id = ?",
                  (novo_hor_id, aula_id))
