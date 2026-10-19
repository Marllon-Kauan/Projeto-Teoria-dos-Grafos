"""
Constrói o grafo completo, aplicando as restrições do usuário e mapeando todas as conexões de conflitos.
"""

from models.turma import Turma
from models.grafo import GrafoSemestre
from database.connection import buscar_turmas, buscar_horarios

def construir_grafo(db_path, id_semestre, horarios_bloqueados, restricoes_professor=None, limites_professor=None, horarios_alocaveis=None):
    restricoes_professor = restricoes_professor or {}
    limites_professor = limites_professor or {}
    
    rows = buscar_turmas(db_path, id_semestre)
    todos_horarios = set(buscar_horarios(db_path))
    if horarios_alocaveis:
        todos_horarios &= set(horarios_alocaveis)
    
    grafo = GrafoSemestre(id_semestre)
    turmas = [] 

    for row in rows:
        turma = Turma(
            tur_id=row[0], tur_codigo=row[1], dis_id=row[2],
            dis_codigo=row[3], dis_nome=row[4], idper_periodo=row[5],
            carga_horaria=row[6], pro_id=row[7], pro_nome=row[8]
        )
        
        turma.dominio_horarios = set(todos_horarios)

        if turma.idper_periodo in [1, 2, 3, 4]:
            if isinstance(horarios_bloqueados, dict):
                bloqueios_turma = horarios_bloqueados.get(str(turma.idper_periodo), horarios_bloqueados.get(turma.idper_periodo, set()))
            else:
                bloqueios_turma = horarios_bloqueados
            turma.dominio_horarios = turma.dominio_horarios - bloqueios_turma

        turma.dominio_horarios = turma.dominio_horarios - restricoes_professor.get(turma.pro_id, set())

        # APLICANDO OS NOVOS LIMITES (Seguidas e Diárias)
        limites = limites_professor.get(turma.pro_id, {})
        turma.max_seguidas = limites.get("seguidas")
        turma.max_diarias = limites.get("diarias")

        grafo.add_vertice(turma)
        turmas.append(turma)

    n = len(turmas)
    for i in range(n):
        for j in range(i + 1, n): 
            t1 = turmas[i]
            t2 = turmas[j]
            motivos = []

            if t1.pro_id == t2.pro_id:
                motivos.append("professor")
            if t1.dis_id == t2.dis_id:
                motivos.append("disciplina")
            if (t1.idper_periodo not in [None, "NULL", ""]) and (t1.idper_periodo == t2.idper_periodo):
                motivos.append("periodo")

            if motivos:
                grafo.add_aresta(t1.tur_id, t2.tur_id, motivos)

    return grafo