# -*- coding: utf-8 -*-
"""
Confere se a grade que esta no banco respeita as regras.

Uso (dentro da pasta src, depois de gerar a grade):
    python verificar_regras.py          # limite de aulas seguidas = 2
    python verificar_regras.py 3        # limite de aulas seguidas = 3

ERRO  = regra violada (a grade nao deveria ter saido assim).
AVISO = nao e erro do algoritmo, e uma preferencia ainda nao imposta.
"""

import os
import sqlite3
import sys
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco_projeto.db")
SEMESTRE = 2
DIAS = {2: "Seg", 3: "Ter", 4: "Qua", 5: "Qui", 6: "Sex", 7: "Sab"}


def tabela_existe(cur, nome):
    return cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nome,)).fetchone()


def main(max_seguidas):
    cur = sqlite3.connect(DB_PATH).cursor()

    cur.execute("""
        SELECT ALO.alo_id, TUR.tur_id, TUR.tur_codigo, TUR.idpro_professor, PRO.pro_nome,
               DIS.dis_id, DIS.dis_nome, DIS.idper_periodo, DIS.dis_cargaHoraria,
               ALO.idsal_sala, ALO.idhor_horario, HOR.hor_diaSemana, HOR.hor_slot
        FROM alo_alocacaoHorarioSala ALO
        JOIN tur_turma TUR ON TUR.tur_id = ALO.idtur_turma
        JOIN dis_disciplina DIS ON DIS.dis_id = TUR.iddis_disciplina
        JOIN pro_professor PRO ON PRO.pro_id = TUR.idpro_professor
        JOIN hor_horario HOR ON HOR.hor_id = ALO.idhor_horario
        WHERE TUR.idsem_semestre = ?""", (SEMESTRE,))
    aulas = [dict(zip(
        ["alo", "tur", "codigo", "pro", "pro_nome", "dis", "dis_nome", "per", "carga",
         "sala", "hor", "dia", "slot"], r)) for r in cur.fetchall()]

    if not aulas:
        print("Nao ha aulas no banco. Gere a grade primeiro.")
        return

    erros, avisos = [], []

    def rotulo(a):
        return "%s (turma %s)" % (a["dis_nome"], a["codigo"])

    # 1-4) conflitos no mesmo horario
    por_horario = defaultdict(list)
    for a in aulas:
        por_horario[a["hor"]].append(a)
    for hor, grupo in por_horario.items():
        quando = "%s %s" % (DIAS[grupo[0]["dia"]], grupo[0]["slot"])
        for i in range(len(grupo)):
            for j in range(i + 1, len(grupo)):
                x, y = grupo[i], grupo[j]
                if x["pro"] == y["pro"]:
                    erros.append("[professor] %s da aula em %s e em %s no mesmo horario (%s)"
                                 % (x["pro_nome"], rotulo(x), rotulo(y), quando))
                if x["per"] is not None and x["per"] == y["per"]:
                    erros.append("[periodo] %do periodo tem %s e %s ao mesmo tempo (%s)"
                                 % (x["per"], rotulo(x), rotulo(y), quando))
                if x["dis"] == y["dis"]:
                    erros.append("[disciplina] duas turmas de %s no mesmo horario (%s)"
                                 % (x["dis_nome"], quando))
                if x["sala"] == y["sala"]:
                    erros.append("[sala] sala %s usada por %s e %s ao mesmo tempo (%s)"
                                 % (x["sala"], rotulo(x), rotulo(y), quando))

    # 5) restricoes de professor
    if tabela_existe(cur, "res_restricao"):
        restr = defaultdict(set)
        for pro, hor in cur.execute("SELECT idpro_professor, idhor_horario FROM res_restricao"):
            restr[pro].add(hor)
        for a in aulas:
            if a["hor"] in restr[a["pro"]]:
                erros.append("[restricao] %s esta com aula em %s num horario proibido (%s %s)"
                             % (a["pro_nome"], rotulo(a), DIAS[a["dia"]], a["slot"]))

    # 6) horarios bloqueados (so 1o ao 4o periodo)
    if tabela_existe(cur, "blq_bloqueio"):
        bloq = {r[0] for r in cur.execute("SELECT idhor_horario FROM blq_bloqueio")}
        for a in aulas:
            if a["per"] in (1, 2, 3, 4) and a["hor"] in bloq:
                erros.append("[bloqueio] %s esta num horario bloqueado (%s %s)"
                             % (rotulo(a), DIAS[a["dia"]], a["slot"]))

    # 7) quantidade de aulas por turma (carga horaria // 15)
    turmas = {}
    for a in aulas:
        turmas.setdefault(a["tur"], []).append(a)
    for tur, lista in turmas.items():
        esperado = lista[0]["carga"] // 15
        if len(lista) != esperado:
            erros.append("[carga] %s tem %d aula(s), esperado %d"
                         % (rotulo(lista[0]), len(lista), esperado))

    # 8) aulas seguidas no mesmo dia da mesma turma
    #    ERRO se o professor tem limite cadastrado; AVISO (limite do argumento) para os demais.
    limites = {}
    if tabela_existe(cur, "pre_preferencia"):
        limites = dict(cur.execute("SELECT idpro_professor, pre_maxSeguidas FROM pre_preferencia"))
    for tur, lista in turmas.items():
        limite = limites.get(lista[0]["pro"])
        por_dia = defaultdict(list)
        for a in lista:
            por_dia[a["dia"]].append(ord(a["slot"]) - ord("A"))
        for dia, slots in por_dia.items():
            slots.sort()
            maior = atual = 1
            for i in range(1, len(slots)):
                atual = atual + 1 if slots[i] == slots[i - 1] + 1 else 1
                maior = max(maior, atual)
            msg = "[seguidas] %s (Prof. %s) tem %d aulas seguidas na %s" % (
                rotulo(lista[0]), lista[0]["pro_nome"], maior, DIAS[dia])
            if limite and maior > limite:
                erros.append(msg + " (limite do professor: %d)" % limite)
            elif not limite and maior > max_seguidas:
                avisos.append(msg)

    print("Aulas conferidas: %d | Turmas: %d\n" % (len(aulas), len(turmas)))
    for e in erros:
        print("ERRO  ", e)
    for w in avisos:
        print("AVISO ", w)
    if not erros:
        print("OK - nenhuma regra violada.")
    print("\n%d erro(s), %d aviso(s)." % (len(erros), len(avisos)))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
