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

SEMESTRE_ID = 2          
ANO = 2026               

DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
DIAS_LONGO = {
    "Seg": "Segunda", "Ter": "Terça", "Qua": "Quarta",
    "Qui": "Quinta", "Sex": "Sexta", "Sab": "Sábado",
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

# Status de disponibilidade das salas (SA04/SA06).
STATUS_DISPONIVEL = "Disponível"
STATUS_INDISPONIVEL = "Indisponível"


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
    Confere que o banco foi criado (setup_db.py), cria as tabelas novas
    usadas pelo front e acrescenta as colunas de disponibilidade da tabela sal_sala
    e de carga horária/eletiva na tabela dis_disciplina, se faltarem.
    A migracao nao apaga nem recria os dados existentes.
    """
    with conexao() as c:
        existentes = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "hor_horario" not in existentes:
            raise RuntimeError(
                "Banco sem tabelas em %s. Rode primeiro: python setup_db.py" % DB_PATH)
        
        if "sal_sala" in existentes:
            colunas_sala = {r[1] for r in c.execute("PRAGMA table_info(sal_sala)")}
            if "sal_status" not in colunas_sala:
                c.execute("ALTER TABLE sal_sala ADD COLUMN sal_status TEXT NOT NULL "
                          "DEFAULT '%s'" % STATUS_DISPONIVEL)
            if "sal_motivo" not in colunas_sala:
                c.execute("ALTER TABLE sal_sala ADD COLUMN sal_motivo TEXT")

        # Verificação e migração de colunas na tabela dis_disciplina (DI01/DI04)
        if "dis_disciplina" in existentes:
            colunas_dis = {r[1] for r in c.execute("PRAGMA table_info(dis_disciplina)")}
            if "dis_cargaHoraria" not in colunas_dis:
                c.execute("ALTER TABLE dis_disciplina ADD COLUMN dis_cargaHoraria INT NOT NULL DEFAULT 60")
            if "dis_eletiva" not in colunas_dis:
                c.execute("ALTER TABLE dis_disciplina ADD COLUMN dis_eletiva INT NOT NULL DEFAULT 0")
                
        for dia, slot in HORARIOS_DO_FRONT:
            if not c.execute("SELECT 1 FROM hor_horario WHERE hor_diaSemana = ? AND hor_slot = ?",
                             (dia, slot)).fetchone():
                novo = (c.execute("SELECT MAX(hor_id) FROM hor_horario").fetchone()[0] or 0) + 1
                ini, fim = FAIXAS[SLOTS.index(slot)]
                c.execute(
                    "INSERT INTO hor_horario (hor_id, hor_diaSemana, hor_slot, hor_horaInicio, hor_horaFim) "
                    "VALUES (?, ?, ?, ?, ?)", (novo, dia, slot, ini, fim))

        # Tabela de restrições.
        if "res_restricao" not in existentes:
            c.execute("""
                CREATE TABLE res_restricao (
                    res_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idpro_professor INT NOT NULL,
                    idhor_horario INT NOT NULL,
                    idsem_semestre INT NOT NULL,
                    res_motivo VARCHAR(200)
                )""")
        else:
            colunas_res = {r[1] for r in c.execute("PRAGMA table_info(res_restricao)")}
            if "idsem_semestre" not in colunas_res:
                c.execute("ALTER TABLE res_restricao ADD COLUMN idsem_semestre INT NOT NULL DEFAULT 1")

        # Tabela de preferências.
        if "pre_preferencia" not in existentes:
            c.execute("""
                CREATE TABLE pre_preferencia (
                    idpro_professor INT,
                    idsem_semestre INT,
                    pre_maxSeguidas INT NOT NULL,
                    pre_maxDiarias INT NOT NULL,
                    PRIMARY KEY (idpro_professor, idsem_semestre)
                )""")
        else:
            colunas_pre = {r[1] for r in c.execute("PRAGMA table_info(pre_preferencia)")}
            if "idsem_semestre" not in colunas_pre or "pre_maxDiarias" not in colunas_pre:
                c.execute("ALTER TABLE pre_preferencia RENAME TO pre_preferencia_antigo")
                c.execute("""
                    CREATE TABLE pre_preferencia (
                        idpro_professor INT,
                        idsem_semestre INT,
                        pre_maxSeguidas INT NOT NULL,
                        pre_maxDiarias INT NOT NULL,
                        PRIMARY KEY (idpro_professor, idsem_semestre)
                    )""")
                c.execute("""
                    INSERT INTO pre_preferencia (idpro_professor, idsem_semestre, pre_maxSeguidas, pre_maxDiarias)
                    SELECT idpro_professor, 1, pre_maxSeguidas, 4
                    FROM pre_preferencia_antigo
                """)
                c.execute("DROP TABLE pre_preferencia_antigo")

        # Tabela de bloqueios.
        if "blq_bloqueio" not in existentes:
            c.execute("""
                CREATE TABLE blq_bloqueio (
                    idper_periodo INT NOT NULL,
                    idhor_horario INT NOT NULL,
                    idsem_semestre INT NOT NULL,
                    PRIMARY KEY (idper_periodo, idhor_horario, idsem_semestre)
                )""")
        else:
            colunas_bloqueio = {r[1] for r in c.execute("PRAGMA table_info(blq_bloqueio)")}
            if "idsem_semestre" not in colunas_bloqueio:
                c.execute("ALTER TABLE blq_bloqueio RENAME TO blq_bloqueio_antigo")
                c.execute("""
                    CREATE TABLE blq_bloqueio (
                        idper_periodo INT NOT NULL,
                        idhor_horario INT NOT NULL,
                        idsem_semestre INT NOT NULL,
                        PRIMARY KEY (idper_periodo, idhor_horario, idsem_semestre)
                    )""")
                
                if "idper_periodo" not in colunas_bloqueio:
                    c.execute("""
                        INSERT INTO blq_bloqueio (idper_periodo, idhor_horario, idsem_semestre)
                        SELECT periodo.idper_periodo, antigo.idhor_horario, 1
                        FROM blq_bloqueio_antigo AS antigo
                        CROSS JOIN (
                            SELECT 1 AS idper_periodo UNION ALL SELECT 2
                            UNION ALL SELECT 3 UNION ALL SELECT 4
                        ) AS periodo
                    """)
                else:
                    c.execute("""
                        INSERT INTO blq_bloqueio (idper_periodo, idhor_horario, idsem_semestre)
                        SELECT idper_periodo, idhor_horario, 1
                        FROM blq_bloqueio_antigo
                    """)
                c.execute("DROP TABLE blq_bloqueio_antigo")


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
    """Horarios que o algoritmo do back usa: todos (segunda a sabado, slots A a G)."""
    return set(_mapa_horarios()[0].keys())


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
    """{codigo: {id, cod, nome, periodo, cor, carga_horaria, eletiva}}"""
    with conexao() as c:
        linhas = c.execute(
            "SELECT dis_id, dis_codigo, dis_nome, idper_periodo, dis_cargaHoraria, dis_eletiva "
            "FROM dis_disciplina ORDER BY dis_nome").fetchall()
    return {
        r["dis_codigo"]: {
            "id": r["dis_id"],
            "cod": r["dis_codigo"],
            "nome": r["dis_nome"],
            "periodo": r["idper_periodo"],
            "cor": (r["dis_id"] % 4) + 1,
            "carga_horaria": r["dis_cargaHoraria"],
            "eletiva": bool(r["dis_eletiva"]),
        } for r in linhas
    }

def buscar_disciplina(dis_id):
    for dis in disciplinas().values():
        if dis["id"] == dis_id:
            return dis
    return None


def criar_disciplina(codigo, nome, periodo, carga, eletiva):
    codigo = (codigo or "").strip().upper()
    nome = (nome or "").strip()
    
    if not codigo or not nome or carga is None or carga <= 0:
        return "Preencha os campos obrigatórios e informe uma carga horária maior que zero."
    if not eletiva and not periodo:
        return "Disciplinas não eletivas exigem a seleção de um período curricular específico."
        
    with conexao() as c:
        if c.execute("SELECT 1 FROM dis_disciplina WHERE dis_codigo = ?", (codigo,)).fetchone():
            return f"O código '{codigo}' já está em uso por outra disciplina."
            
        novo = (c.execute("SELECT MAX(dis_id) FROM dis_disciplina").fetchone()[0] or 0) + 1
        c.execute(
            "INSERT INTO dis_disciplina (dis_id, dis_codigo, dis_nome, idper_periodo, dis_cargaHoraria, dis_eletiva) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (novo, codigo, nome, periodo, carga, 1 if eletiva else 0)
        )
    return None

def atualizar_disciplina(dis_id, codigo, nome, periodo, carga, eletiva):
    codigo = (codigo or "").strip().upper()
    nome = (nome or "").strip()
    
    if not codigo or not nome or carga is None or carga <= 0:
        return "Preencha os campos obrigatórios e informe uma carga horária maior que zero."
    if not eletiva and not periodo:
        return "Disciplinas não eletivas exigem a seleção de um período curricular específico."
        
    with conexao() as c:
        if c.execute("SELECT 1 FROM dis_disciplina WHERE dis_codigo = ? AND dis_id <> ?", (codigo, dis_id)).fetchone():
            return f"O código '{codigo}' já está em uso por outra disciplina."
            
        c.execute(
            "UPDATE dis_disciplina SET dis_codigo = ?, dis_nome = ?, idper_periodo = ?, dis_cargaHoraria = ?, dis_eletiva = ? "
            "WHERE dis_id = ?",
            (codigo, nome, periodo, carga, 1 if eletiva else 0, dis_id)
        )
    return None

def excluir_disciplina(dis_id):
    with conexao() as c:
        turmas_vinculadas = c.execute(
            "SELECT tur_codigo FROM tur_turma WHERE iddis_disciplina = ? AND idsem_semestre = ?",
            (dis_id, SEMESTRE_ID)
        ).fetchall()
        
        if turmas_vinculadas:
            codigos = ", ".join([r[0] for r in turmas_vinculadas])
            return f"A exclusão foi impedida pois a disciplina possui turmas vinculadas no semestre ativo ({codigos}). Remova as turmas ou altere a disciplina associada a elas antes de prosseguir."
            
        c.execute("DELETE FROM dis_disciplina WHERE dis_id = ?", (dis_id,))
    return None

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


def salas():
    """Salas cadastradas, com status e motivo, para a tela de salas."""
    with conexao() as c:
        linhas = c.execute(
            "SELECT sal_id, sal_bloco, sal_numero, sal_status, sal_motivo "
            "FROM sal_sala ORDER BY sal_bloco, sal_numero").fetchall()
    return [{
        "id": r["sal_id"],
        "nome": "%s-%s" % (r["sal_bloco"], r["sal_numero"]),
        "bloco": r["sal_bloco"],
        "numero": r["sal_numero"],
        "status": r["sal_status"] or STATUS_DISPONIVEL,
        "motivo": r["sal_motivo"],
    } for r in linhas]


def salas_da_turma(turma_id):
    """Salas usadas atualmente pelas aulas da turma."""
    with conexao() as c:
        linhas = c.execute("""
            SELECT DISTINCT SAL.sal_id, SAL.sal_bloco, SAL.sal_numero
            FROM alo_alocacaoHorarioSala ALO
            JOIN sal_sala SAL ON SAL.sal_id = ALO.idsal_sala
            WHERE ALO.idtur_turma = ?
            ORDER BY SAL.sal_bloco, SAL.sal_numero""", (turma_id,)).fetchall()
    return [{"id": r["sal_id"], "nome": "%s-%s" % (r["sal_bloco"], r["sal_numero"])}
            for r in linhas]


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
            WHERE R.idsem_semestre = ?
            ORDER BY P.pro_nome, R.idhor_horario""", (SEMESTRE_ID,)).fetchall()
    resultado = []
    for r in linhas:
        pos = dia_h(r["idhor_horario"])
        if pos is None: continue
        resultado.append({
            "id": r["res_id"], "prof": r["pro_nome"], "prof_id": r["idpro_professor"],
            "dia": pos[0], "h": pos[1], "hor_id": r["idhor_horario"], "motivo": r["res_motivo"],
        })
    return resultado


def restricoes_por_professor():
    """{pro_id: {hor_id, ...}} no formato que o builder.py recebe."""
    mapa = {}
    for r in restricoes():
        mapa.setdefault(r["prof_id"], set()).add(r["hor_id"])
    return mapa


def preferencias():
    #Limite de aulas seguidas no mesmo dia, por professor.
    with conexao() as c:
        linhas = c.execute("""
            SELECT P.pro_id, P.pro_nome, F.pre_maxSeguidas, F.pre_maxDiarias
            FROM pre_preferencia F JOIN pro_professor P ON P.pro_id = F.idpro_professor
            WHERE F.idsem_semestre = ?
            ORDER BY P.pro_nome""", (SEMESTRE_ID,)).fetchall()
    return [{"prof_id": r[0], "prof": r[1], "max_seg": r[2], "max_dia": r[3]} for r in linhas]

def limites_por_professor():
    return {p["prof_id"]: {"seguidas": p["max_seg"], "diarias": p["max_dia"]} for p in preferencias()}

def max_seguidas_por_professor():
    """{pro_id: n} no formato que o builder.py recebe."""
    return {p["prof_id"]: p["max_seg"] for p in preferencias()}


def bloqueados_por_periodo():
    #{periodo: {hor_id, ...}} com os bloqueios de cada periodo basico.
    resultado = {periodo: set() for periodo in PERIODOS_BLOQUEAVEIS}
    with conexao() as c:
        for r in c.execute("SELECT idper_periodo, idhor_horario FROM blq_bloqueio WHERE idsem_semestre = ?", (SEMESTRE_ID,)):
            if r[0] in resultado: resultado[r[0]].add(r[1])
    return resultado


# ---------------------------------------------------------------- escrita

def criar_turma(cod_disciplina, codigo_turma, prof_nome):
    """Retorna None se cadastrou, ou a mensagem de erro."""
    dis = disciplinas().get(cod_disciplina)
    pro_id = _prof_id(prof_nome)
    if dis is None or pro_id is None:
        return "Disciplina ou professor inválido."
    with conexao() as c:
        if c.execute("SELECT 1 FROM tur_turma WHERE tur_codigo = ? AND idsem_semestre = ?",
                     (codigo_turma, SEMESTRE_ID)).fetchone():
            return "Já existe uma turma com o código %s neste semestre." % codigo_turma
        novo = (c.execute("SELECT MAX(tur_id) FROM tur_turma").fetchone()[0] or 0) + 1
        c.execute(
            "INSERT INTO tur_turma (tur_id, tur_codigo, idpro_professor, iddis_disciplina, idsem_semestre) "
            "VALUES (?, ?, ?, ?, ?)", (novo, codigo_turma, pro_id, dis["id"], SEMESTRE_ID))
    return None


def atualizar_turma(turma_id, cod_disciplina, codigo_turma, prof_nome, sala_id=None):
    atual = buscar_turma(turma_id)
    if atual is None:
        return "Turma não encontrada.", None

    dis = disciplinas().get(cod_disciplina)
    pro_id = _prof_id(prof_nome)
    if dis is None or pro_id is None:
        return "Disciplina ou professor inválido.", None
        
    if not isinstance(codigo_turma, str) or len(codigo_turma) != 2:
        return "Código da turma inválido.", None

    mudou_disciplina = dis["id"] != atual["dis_id"]
    mudou_professor = pro_id != atual["prof_id"]
    aulas_turma = [a for a in aulas() if a["turma"] == turma_id]
    outras_aulas = [a for a in aulas() if a["turma"] != turma_id]

    #Novo professor: restricoes e aulas ja existentes dele no mesmo horario.
    if mudou_professor and not mudou_disciplina and aulas_turma:
        restritas = restricoes_por_professor().get(pro_id, set())
        turmas_por_id = {t["id"]: t for t in turmas()}
        for aula in aulas_turma:
            pos = dia_h(aula["hor_id"])
            quando = ("%s, %s" % (DIAS_LONGO[pos[0]], horarios()[pos[1]])
                      if pos else "o horario atual")
            if aula["hor_id"] in restritas:
                return ("O professor %s tem restrição em %s." % (prof_nome, quando), None)
            for outra in outras_aulas:
                if outra["hor_id"] != aula["hor_id"]:
                    continue
                t2 = turmas_por_id.get(outra["turma"])
                if t2 is not None and t2["prof_id"] == pro_id:
                    return ("O professor %s já tem aula em %s." % (prof_nome, quando), None)

    #Nova sala: precisa existir, estar disponível e estar livre em todos os horarios da turma.
    if sala_id is not None:
        todas_salas = salas()
        salas_validas = {s["id"]: s["nome"] for s in todas_salas}
        
        if sala_id not in salas_validas:
            return "Sala inválida.", None
            
        sala_selecionada = next((s for s in todas_salas if s["id"] == sala_id), None)
        if sala_selecionada and sala_selecionada["status"] == STATUS_INDISPONIVEL:
            return "A sala selecionada está indisponível.", None
            
        if aulas_turma and not (mudou_disciplina or mudou_professor):
            for aula in aulas_turma:
                for outra in outras_aulas:
                    if outra["hor_id"] == aula["hor_id"] and outra["sal_id"] == sala_id:
                        pos = dia_h(aula["hor_id"])
                        quando = ("%s, %s" % (DIAS_LONGO[pos[0]], horarios()[pos[1]])
                                  if pos else "o horário atual")
                        return ("A sala %s já está ocupada em %s."
                                % (salas_validas[sala_id], quando), None)

    with conexao() as c:
        duplicada = c.execute(
            "SELECT 1 FROM tur_turma WHERE tur_codigo = ? AND idsem_semestre = ? AND tur_id <> ?",
            (codigo_turma, SEMESTRE_ID, turma_id)).fetchone()
        if duplicada:
            return ("Já existe uma turma com o código %s neste semestre."
                    % codigo_turma, None)

        #Remove as alocações se mudar a disciplina ou o professor.
        if mudou_disciplina or mudou_professor:
            c.execute("DELETE FROM alo_alocacaoHorarioSala WHERE idtur_turma = ?", (turma_id,))

        c.execute(
            "UPDATE tur_turma SET tur_codigo = ?, idpro_professor = ?, iddis_disciplina = ? "
            "WHERE tur_id = ?",
            (codigo_turma, pro_id, dis["id"], turma_id))

        #Atualiza a sala apenas se não mudou a disciplina nem o professor.
        if sala_id is not None and aulas_turma and not (mudou_disciplina or mudou_professor):
            c.execute(
                "UPDATE alo_alocacaoHorarioSala SET idsal_sala = ? WHERE idtur_turma = ?",
                (sala_id, turma_id))

    aviso = None
    #Exibe o aviso de gerar grade se mudar a disciplina ou o professor.
    if (mudou_disciplina or mudou_professor) and aulas_turma:
        aviso = ("As alocações da turma foram removidas; use \"Gerar grade\" "
                 "para alocá-las novamente.")
    return None, aviso


def excluir_turma(turma_id):
    with conexao() as c:
        c.execute("DELETE FROM alo_alocacaoHorarioSala WHERE idtur_turma = ?", (turma_id,))
        c.execute("DELETE FROM tur_turma WHERE tur_id = ?", (turma_id,))


def criar_sala(bloco, numero):
    """Cadastra uma sala. Retorna None ou a mensagem de erro."""
    bloco = (bloco or "").strip().upper()
    if not bloco or len(bloco) > 20:
        return "Informe o bloco e o número da sala."
    try:
        numero = int(numero)
    except (TypeError, ValueError):
        return "Número de sala inválido."
    # 999999999 evita estourar o inteiro do SQLite e mantem a numeracao
    # dentro de um limite plausivel para salas.
    if numero <= 0 or numero > 999999999:
        return "Número de sala inválido."
    with conexao() as c:
        existente = c.execute(
            "SELECT 1 FROM sal_sala WHERE UPPER(sal_bloco) = ? AND sal_numero = ?",
            (bloco, numero)).fetchone()
        if existente:
            return "Já existe uma sala com o bloco %s e o número %s." % (bloco, numero)
        novo = (c.execute("SELECT MAX(sal_id) FROM sal_sala").fetchone()[0] or 0) + 1
        c.execute(
            "INSERT INTO sal_sala (sal_id, sal_bloco, sal_numero, sal_status, sal_motivo) "
            "VALUES (?, ?, ?, ?, NULL)",
            (novo, bloco, numero, STATUS_DISPONIVEL))
    return None


def atualizar_disponibilidade_sala(sala_id, status, motivo=None):
    if status not in (STATUS_DISPONIVEL, STATUS_INDISPONIVEL):
        return "Status de sala inválido.", None
    motivo = (motivo or "").strip()
    if status == STATUS_DISPONIVEL:
        motivo = None          
    else:
        motivo = motivo or None
        
    aviso = None
    with conexao() as c:
        if status == STATUS_INDISPONIVEL:
            em_uso = c.execute(
                "SELECT COUNT(*) FROM alo_alocacaoHorarioSala WHERE idsal_sala = ?",
                (sala_id,)
            ).fetchone()[0]
            if em_uso > 0:
                aviso = "Atenção: A sala possui %d aula(s) alocada(s) que permanecerão nela até a próxima geração da grade." % em_uso
                
        cursor = c.execute(
            "UPDATE sal_sala SET sal_status = ?, sal_motivo = ? WHERE sal_id = ?",
            (status, motivo, sala_id))
        if cursor.rowcount == 0:
            return "Sala não encontrada.", None
            
    return None, aviso

def excluir_sala(sala_id):
    """Exclui a sala se não houver alocações. Retorna None ou a mensagem de erro."""
    with conexao() as c:
        if not c.execute("SELECT 1 FROM sal_sala WHERE sal_id = ?",
                         (sala_id,)).fetchone():
            return "Sala não encontrada."
        em_uso = c.execute(
            "SELECT COUNT(*) FROM alo_alocacaoHorarioSala WHERE idsal_sala = ?",
            (sala_id,)).fetchone()[0]
        if em_uso:
            return ("Não é possível excluir: a sala possui %d aula(s) alocada(s)."
                    % em_uso)
        c.execute("DELETE FROM sal_sala WHERE sal_id = ?", (sala_id,))
    return None


def criar_restricao(prof_nome, dia, h_val, motivo):
    pro_id = _prof_id(prof_nome)
    if pro_id is None:
        return "erro"

    if h_val == "todos":
        hids = [hor_id(dia, i) for i in range(7)]
    else:
        hids = [hor_id(dia, int(h_val))]
        
    status_final = "criado"
    
    with conexao() as c:
        for hid in hids:
            if hid is None:
                continue
                
            #Verifica se já existe uma restrição para esse professor nesse horário e semestre.
            existente = c.execute(
                "SELECT 1 FROM res_restricao WHERE idpro_professor = ? AND idhor_horario = ? AND idsem_semestre = ?", 
                (pro_id, hid, SEMESTRE_ID)
            ).fetchone()
            
            if existente:
                #Se já existe, atualiza o motivo para evitar duplicidade.
                c.execute(
                    "UPDATE res_restricao SET res_motivo = ? WHERE idpro_professor = ? AND idhor_horario = ? AND idsem_semestre = ?",
                    (motivo, pro_id, hid, SEMESTRE_ID)
                )
                status_final = "atualizado"
            else:
                #Se não existe, cria a nova restrição.
                c.execute(
                    "INSERT INTO res_restricao (idpro_professor, idhor_horario, idsem_semestre, res_motivo) VALUES (?, ?, ?, ?)",
                    (pro_id, hid, SEMESTRE_ID, motivo)
                )
                
    return status_final

def excluir_restricao(restricao_id):
    with conexao() as c:
        c.execute("DELETE FROM res_restricao WHERE res_id = ?", (restricao_id,))


def salvar_preferencia(prof_nome, max_seg, max_dia):
    pro_id = _prof_id(prof_nome)
    if pro_id is None: return False
    with conexao() as c:
        c.execute("INSERT OR REPLACE INTO pre_preferencia (idpro_professor, idsem_semestre, pre_maxSeguidas, pre_maxDiarias) VALUES (?, ?, ?, ?)", (pro_id, SEMESTRE_ID, max_seg, max_dia))
    return True


def excluir_preferencia(pro_id):
    with conexao() as c:
        c.execute("DELETE FROM pre_preferencia WHERE idpro_professor = ?", (pro_id,))


def salvar_bloqueados(periodo, ids):
    if periodo not in PERIODOS_BLOQUEAVEIS: return set()
    validos = set(_mapa_horarios()[0].keys())
    ids = {i for i in ids if i in validos}
    with conexao() as c:
        c.execute("DELETE FROM blq_bloqueio WHERE idper_periodo = ? AND idsem_semestre = ?", (periodo, SEMESTRE_ID))
        c.executemany("INSERT INTO blq_bloqueio (idper_periodo, idhor_horario, idsem_semestre) VALUES (?, ?, ?)", [(periodo, i, SEMESTRE_ID) for i in ids])
    return ids


def mover_aula(aula_id, novo_hor_id):
    with conexao() as c:
        c.execute("UPDATE alo_alocacaoHorarioSala SET idhor_horario = ? WHERE alo_id = ?",
                  (novo_hor_id, aula_id))