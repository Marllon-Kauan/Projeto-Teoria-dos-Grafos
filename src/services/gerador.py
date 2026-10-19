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
    if not isinstance(horarios_bloqueados, dict):
        horarios_bloqueados = set(horarios_bloqueados)

    grafo = construir_grafo(db_path, id_semestre, horarios_bloqueados, restricoes_prof, max_seguidas_prof, horarios_alocaveis)
    ordem = ordenar_turmas(grafo)

    #Executa ambas as etapas sem interromper o processo.
    sem_horario = alocar_horarios(grafo, ordem)
    sem_sala = alocar_salas(db_path, grafo, ordem)

    turmas_com_erro = []
    
    if sem_horario:
        turmas_com_erro.extend([_descricao(t) + " (Sem horário)" for t in sem_horario])
    
    if sem_sala:
        turmas_com_erro.extend([_descricao(t) + " (Sem sala)" for t in sem_sala])

    #Se a lista de erros estiver vazia, foi 100% de sucesso. Caso não, é parcial.
    return {
        "ok": len(turmas_com_erro) == 0,
        "parcial": len(turmas_com_erro) > 0,
        "turmas": turmas_com_erro
    }