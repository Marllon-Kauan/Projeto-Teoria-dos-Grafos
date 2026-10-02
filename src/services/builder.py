"""
Constrói o grafo completo, aplicando as restrições do usuário e mapeando todas as conexões de conflitos.
"""

from models.turma import Turma
from models.grafo import GrafoSemestre
from database.connection import buscar_turmas, buscar_horarios

#Molda o grafo completo antes do algoritmo atuar.
def construir_grafo(db_path, id_semestre, horarios_bloqueados):
    rows = buscar_turmas(db_path, id_semestre) #Pega todas as informações de turma daquele semestre.
    todos_horarios = set(buscar_horarios(db_path)) #Pega todos os IDs de horário.
    
    #Inicializa o Grafo.
    grafo = GrafoSemestre(id_semestre)
    turmas = [] 

    #Passa pelos dados do banco.
    for row in rows:
        #Cria uma instância de turma.
        turma = Turma(
            tur_id=row[0], tur_codigo=row[1], dis_id=row[2],
            dis_codigo=row[3], dis_nome=row[4], idper_periodo=row[5],
            carga_horaria=row[6], pro_id=row[7], pro_nome=row[8]
        )
        
        #A turma recebe a permissão de ocupar todos os horários possíveis.
        turma.dominio_horarios = set(todos_horarios)

        #Se a turma pertencer aos períodos básicos (1 a 4), restrição de horários bloqueados pelo usuário.
        if turma.idper_periodo in [1, 2, 3, 4]:
            turma.dominio_horarios = turma.dominio_horarios - horarios_bloqueados

        #Adiciona a turma como um vértice no grafo.
        grafo.add_vertice(turma)
        turmas.append(turma)

    #Inicia a criação das arestas (conflitos) comparando as turmas.
    n = len(turmas)
    for i in range(n):
        for j in range(i + 1, n): 
            t1 = turmas[i]
            t2 = turmas[j]
            motivos = [] #Guarda os motivos do conflito.

            #Se duas turmas tiverem o mesmo professor, tem conflito.
            if t1.pro_id == t2.pro_id:
                motivos.append("professor")

            #Se duas turmas pertencerem à mesma disciplina, tem conflito.
            if t1.dis_id == t2.dis_id:
                motivos.append("disciplina")

            #Se duas turmas fizerem parte do mesmo período, tem conflito.
            if t1.idper_periodo is not None and t1.idper_periodo == t2.idper_periodo:
                motivos.append("periodo")

            #Se houve algum conflito listado
            if motivos:
                #Adiciona a aresta conectando esses dois vértices no grafo.
                grafo.add_aresta(t1.tur_id, t2.tur_id, motivos)

    #Devolve o grafo.
    return grafo