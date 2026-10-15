# -*- coding: utf-8 -*-
"""
Roda o algoritmo completo (grafo -> horarios -> salas) e devolve o resultado,
em vez de imprimir no terminal como o main.py faz. E o que o front chama.
"""

from services.builder import construir_grafo
from services.algorithm import ordenar_turmas, alocar_horarios
from services.saver import alocar_salas


def _descricao(turma):
    return "Turma %s: %s (Prof: %s)" % (turma.tur_codigo, turma.dis_nome, turma.pro_nome)


def gerar_grade(db_path, id_semestre, horarios_bloqueados, restricoes_prof, max_seguidas_prof=None, horarios_alocaveis=None):
    """
    Retorna {"ok": bool, "etapa": "horario"|"sala"|None, "turmas": [descricoes]}.
    Se falhar, o banco continua com a grade anterior.

    horarios_bloqueados pode ser:
      - dict {periodo: {hor_id, ...}}  (formato do repositorio.bloqueados_por_periodo)
      - conjunto/lista global de hor_id (compatibilidade com o main.py)
    """
    # Nao usar set() em cima do dict: isso viraria o conjunto das chaves {1, 2, 3, 4}.
    if not isinstance(horarios_bloqueados, dict):
        horarios_bloqueados = set(horarios_bloqueados)

    grafo = construir_grafo(db_path, id_semestre, horarios_bloqueados, restricoes_prof, max_seguidas_prof, horarios_alocaveis)
    ordem = ordenar_turmas(grafo)

    sem_horario = alocar_horarios(grafo, ordem)
    if sem_horario:
        return {"ok": False, "etapa": "horario", "turmas": [_descricao(t) for t in sem_horario]}

    sem_sala = alocar_salas(db_path, grafo, ordem)
    if sem_sala:
        return {"ok": False, "etapa": "sala", "turmas": [_descricao(t) for t in sem_sala]}

    return {"ok": True, "etapa": None, "turmas": []}