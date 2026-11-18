"""
Confere se a grade que esta no banco respeita as regras.

Uso (dentro da pasta src, depois de gerar a grade):
    python verificar_regras.py          # limite de aulas seguidas = 2
    python verificar_regras.py 3        # limite de aulas seguidas = 3

Usa o mesmo semestre ativo do app (repositorio.SEMESTRE_ID).

ERRO  = regra violada (a grade nao deveria ter saido assim).
AVISO = nao e erro do algoritmo, e uma preferencia ainda nao imposta.
"""

import os
import sqlite3
import sys
from collections import defaultdict

from repositorio import PERIODOS_BLOQUEAVEIS, SEMESTRE_ID as SEMESTRE

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco_projeto.db")
DIAS = {2: "Seg", 3: "Ter", 4: "Qua", 5: "Qui", 6: "Sex", 7: "Sab"}


def tabela_existe(cur, nome):
    return cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nome,)).fetchone()


def maior_sequencia(slots):
    """Maior quantidade de slots consecutivos (ex.: [0, 1, 2, 4] -> 3)."""
    slots = sorted(slots)
    maior = atual = 1 if slots else 0
    for i in range(1, len(slots)):
        atual = atual + 1 if slots[i] == slots[i - 1] + 1 else 1
        maior = max(maior, atual)
    return maior


def main(max_seguidas, db_path=None):
    """Imprime o relatorio e devolve (erros, avisos)."""
    cur = sqlite3.connect(db_path or DB_PATH).cursor()

    colunas_dis = {r[1] for r in cur.execute("PRAGMA table_info(dis_disciplina)")}
    campo_eletiva = "COALESCE(DIS.dis_eletiva, 0)" if "dis_eletiva" in colunas_dis else "0"

    cur.execute(f"""
        SELECT ALO.alo_id, TUR.tur_id, TUR.tur_codigo, TUR.idpro_professor, PRO.pro_nome,
               DIS.dis_id, DIS.dis_nome, DIS.idper_periodo, DIS.dis_cargaHoraria,
               {campo_eletiva},
               ALO.idsal_sala, ALO.idhor_horario, HOR.hor_diaSemana, HOR.hor_slot
        FROM alo_alocacaoHorarioSala ALO
        JOIN tur_turma TUR ON TUR.tur_id = ALO.idtur_turma
        JOIN dis_disciplina DIS ON DIS.dis_id = TUR.iddis_disciplina
        JOIN pro_professor PRO ON PRO.pro_id = TUR.idpro_professor
        JOIN hor_horario HOR ON HOR.hor_id = ALO.idhor_horario
        WHERE TUR.idsem_semestre = ?""", (SEMESTRE,))
    aulas = [dict(zip(
        ["alo", "tur", "codigo", "pro", "pro_nome", "dis", "dis_nome", "per", "carga",
         "eletiva", "sala", "hor", "dia", "slot"], r)) for r in cur.fetchall()]

    if not aulas:
        print("Nao ha aulas no banco. Gere a grade primeiro.")
        return [], []

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
                if (not x["eletiva"] and not y["eletiva"]
                        and x["per"] is not None and x["per"] == y["per"]):
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
        for pro, hor in cur.execute(
                "SELECT idpro_professor, idhor_horario FROM res_restricao WHERE idsem_semestre = ?",
                (SEMESTRE,)):
            restr[pro].add(hor)
        for a in aulas:
            if a["hor"] in restr[a["pro"]]:
                erros.append("[restricao] %s esta com aula em %s num horario proibido (%s %s)"
                             % (a["pro_nome"], rotulo(a), DIAS[a["dia"]], a["slot"]))

    # 6) horarios bloqueados: cada bloqueio vale so para o seu periodo (1o ao 4o) e nao vale para eletivas
    if tabela_existe(cur, "blq_bloqueio"):
        bloq = defaultdict(set)
        for per, hor in cur.execute(
                "SELECT idper_periodo, idhor_horario FROM blq_bloqueio WHERE idsem_semestre = ?",
                (SEMESTRE,)):
            bloq[per].add(hor)
        for a in aulas:
            if (a["per"] in PERIODOS_BLOQUEAVEIS and not a["eletiva"]
                    and a["hor"] in bloq[a["per"]]):
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

    # 8) limites cadastrados do professor (somando TODAS as turmas dele, como o algoritmo faz)
    limites = {}
    if tabela_existe(cur, "pre_preferencia"):
        for pro, seg, dia in cur.execute(
                "SELECT idpro_professor, pre_maxSeguidas, pre_maxDiarias FROM pre_preferencia "
                "WHERE idsem_semestre = ?", (SEMESTRE,)):
            limites[pro] = (seg, dia)
    aulas_prof = defaultdict(lambda: defaultdict(list))
    for a in aulas:
        aulas_prof[a["pro"]][a["dia"]].append(ord(a["slot"]) - ord("A"))
    for pro, (max_seg, max_dia) in limites.items():
        for dia, slots in aulas_prof.get(pro, {}).items():
            nome = next(a["pro_nome"] for a in aulas if a["pro"] == pro)
            if max_dia and len(slots) > max_dia:
                erros.append("[diarias] Prof. %s tem %d aulas na %s (limite: %d)"
                             % (nome, len(slots), DIAS[dia], max_dia))
            if max_seg and maior_sequencia(slots) > max_seg:
                erros.append("[seguidas] Prof. %s tem %d aulas seguidas na %s (limite: %d)"
                             % (nome, maior_sequencia(slots), DIAS[dia], max_seg))

    # 9) AVISO: aulas seguidas da mesma turma acima do limite do argumento (professores sem limite cadastrado)
    for tur, lista in turmas.items():
        if lista[0]["pro"] in limites:
            continue
        por_dia = defaultdict(list)
        for a in lista:
            por_dia[a["dia"]].append(ord(a["slot"]) - ord("A"))
        for dia, slots in por_dia.items():
            maior = maior_sequencia(slots)
            if maior > max_seguidas:
                avisos.append("[seguidas] %s (Prof. %s) tem %d aulas seguidas na %s" % (
                    rotulo(lista[0]), lista[0]["pro_nome"], maior, DIAS[dia]))

    print("Aulas conferidas: %d | Turmas: %d\n" % (len(aulas), len(turmas)))
    for e in erros:
        print("ERRO  ", e)
    for w in avisos:
        print("AVISO ", w)
    if not erros:
        print("OK - nenhuma regra violada.")
    print("\n%d erro(s), %d aviso(s)." % (len(erros), len(avisos)))
    return erros, avisos


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)