"""
Roda o algoritmo completo (grafo -> horarios -> salas) e devolve o resultado pelo front.
"""

import sqlite3
from services.builder import construir_grafo
from services.algorithm import ordenar_turmas, alocar_horarios
from services.saver import alocar_salas

def _descricao(turma):
    return "Turma %s: %s (Prof: %s)" % (turma.tur_codigo, turma.dis_nome, turma.pro_nome)

def _obter_horarios_do_banco(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hor_id, hor_diaSemana, hor_horaInicio, hor_horaFim FROM hor_horario ORDER BY hor_diaSemana, hor_horaInicio")
        
        horarios = []
        dia_atual = None
        ordem = 0
        
        for r in cursor.fetchall():
            if r[1] != dia_atual:
                dia_atual = r[1]
                ordem = 0  
                
            horarios.append({
                "id": r[0],
                "dia": r[1],
                "ordem": ordem,
                "inicio": r[2],
                "fim": r[3]
            })
            ordem += 1
            
        return horarios

def gerar_grade(db_path, id_semestre, horarios_bloqueados, restricoes_prof, limites_prof=None, horarios_alocaveis=None):
    if not isinstance(horarios_bloqueados, dict):
        horarios_bloqueados = set(horarios_bloqueados)

    #Busca a lista de horários da base de dados.
    horarios_do_banco = _obter_horarios_do_banco(db_path)

    #Se não houver nenhum horário cadastrado no banco, interrompe a geração.
    if not horarios_do_banco:
        return {
            "ok": False,
            "parcial": False,
            "sem_horarios": True,
            "turmas": []
        }

    #Constrói o grafo com os limites.
    grafo = construir_grafo(db_path, id_semestre, horarios_bloqueados, restricoes_prof, limites_prof, horarios_alocaveis)
    ordem = ordenar_turmas(grafo)

    #Executa a alocação passando o mapa de horários.
    sem_horario = alocar_horarios(grafo, ordem, horarios_do_banco)
    
    # Só persiste salas quando todas as turmas receberam horário.
    sem_sala = []
    if not sem_horario:
        sem_sala = alocar_salas(db_path, grafo, ordem)

    turmas_com_erro = []
    
    if sem_horario:
        turmas_com_erro.extend([_descricao(t) + " (Sem horário)" for t in sem_horario])
    
    if sem_sala:
        turmas_com_erro.extend([_descricao(t) + " (Sem sala)" for t in sem_sala])

    return {
        "ok": len(turmas_com_erro) == 0,
        "parcial": len(turmas_com_erro) > 0,
        "turmas": turmas_com_erro
    }