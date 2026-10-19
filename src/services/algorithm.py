"""
Ordena a prioridade das turmas e encaixa os horários duplos ou avulsos sem gerar conflitos.
"""

from collections import deque


#Pega todos os horários já alocados para todas as turmas desse professor.
def horarios_do_professor(grafo, pro_id):
    horarios = []
    for turma in grafo.vertice_turmas.values():
        if turma.pro_id == pro_id:
            horarios.extend(turma.horarios_alocados)
    return horarios

#Conta quantas aulas existem naquele dia específico.
def total_no_dia(horarios, dia_index):
    return sum(1 for h in horarios if (h - 1) // 7 == dia_index)

#Maior quantidade de aulas seguidas no mesmo dia entre os horários informados.
def maior_sequencia_no_dia(horarios):
    por_dia = {}
    for h in horarios:
        por_dia.setdefault((h - 1) // 7, []).append((h - 1) % 7)

    maior = 0
    for slots in por_dia.values():
        slots.sort()
        atual = 0
        for i, s in enumerate(slots):
            atual = atual + 1 if i > 0 and s == slots[i - 1] + 1 else 1
            maior = max(maior, atual)
    return maior

#Define em qual ordem as turmas devem ser resolvidas.
def ordenar_turmas(grafo):
    visitados = set()      #Rastrear as turmas já processadas.
    ordem_alocacao = []    #Lista da ordem final de processamento.
    
    #Ordena os IDs das turmas priorizando as que têm mais conflitos (maior grau).
    turmas_por_grau = sorted(
        grafo.vertice_turmas.keys(),
        key=lambda t_id: grafo.obter_grau(t_id),
        reverse=True
    )
    
    #Garante que grupos não conectados entre si sejam visitados.
    for tur_id_inicial in turmas_por_grau:
        if tur_id_inicial not in visitados:
            fila = deque([tur_id_inicial])
            
            while fila:
                atual = fila.popleft() 
                
                if atual not in visitados:
                    visitados.add(atual)
                    ordem_alocacao.append(atual)
                    
                    vizinhos = list(grafo.adjacencias.get(atual, {}).keys())
                    
                    vizinhos_ordenados = sorted(
                        vizinhos,
                        key=lambda v_id: grafo.obter_grau(v_id),
                        reverse=True
                    )
                    
                    for vizinho in vizinhos_ordenados:
                        if vizinho not in visitados:
                            fila.append(vizinho)
                            
    return ordem_alocacao


#Função que escolhe e distribui os horários.
def alocar_horarios(grafo, ordem_alocacao):
    blocos_geminados = [
        (1, 2), (3, 4), (5, 6),       #Segunda 
        (8, 9), (10, 11), (12, 13),   #Terça   
        (15, 16), (17, 18), (19, 20), #Quarta  
        (22, 23), (24, 25), (26, 27), #Quinta  
        (29, 30), (31, 32), (33, 34), #Sexta   
        (36, 37), (38, 39), (40, 41)  #Sábado  
    ]

    turmas_com_erro = []

    for tur_id in ordem_alocacao:
        turma = grafo.vertice_turmas[tur_id] 
        
        blocos_necessarios = turma.aulas_semanais // 2
        aulas_avulsas_restantes = turma.aulas_semanais % 2
        blocos_alocados = 0
        
        for bloco in blocos_geminados:
            if blocos_alocados >= blocos_necessarios:
                break
                
            h1, h2 = bloco
            
            if h1 not in turma.dominio_horarios or h2 not in turma.dominio_horarios:
                continue

            #Pega todos os horários que o professor já dá aula na semana inteira.
            horarios_prof = horarios_do_professor(grafo, turma.pro_id)

            #Limite de aulas seguidas
            if turma.max_seguidas and maior_sequencia_no_dia(horarios_prof + [h1, h2]) > turma.max_seguidas:
                continue
                
            #Limite total de aulas no dia 
            dia_h1 = (h1 - 1) // 7
            dia_h2 = (h2 - 1) // 7
            if turma.max_diarias:
                if total_no_dia(horarios_prof + [h1, h2], dia_h1) > turma.max_diarias: continue
                if total_no_dia(horarios_prof + [h1, h2], dia_h2) > turma.max_diarias: continue

            conflito = False
            for vizinho_id in grafo.adjacencias.get(tur_id, {}):
                vizinho = grafo.vertice_turmas[vizinho_id]
                if h1 in vizinho.horarios_alocados or h2 in vizinho.horarios_alocados:
                    conflito = True
                    break
                    
            if not conflito:
                turma.horarios_alocados.extend([h1, h2])
                blocos_alocados += 1 
                
        #Lida com aulas ímpares que sobraram.
        if aulas_avulsas_restantes > 0:
            for h in turma.dominio_horarios:
                if h not in turma.horarios_alocados:
                    horarios_prof = horarios_do_professor(grafo, turma.pro_id)

                    #Limite de aulas seguidas para a aula avulsa.
                    if turma.max_seguidas and maior_sequencia_no_dia(horarios_prof + [h]) > turma.max_seguidas:
                        continue
                        
                    #Limite total de aulas no dia para a aula avulsa.
                    dia_h = (h - 1) // 7
                    if turma.max_diarias and total_no_dia(horarios_prof + [h], dia_h) > turma.max_diarias:
                        continue

                    conflito = False
                    for vizinho_id in grafo.adjacencias.get(tur_id, {}):
                        vizinho = grafo.vertice_turmas[vizinho_id]
                        if h in vizinho.horarios_alocados:
                            conflito = True
                            break
                            
                    if not conflito:
                        turma.horarios_alocados.append(h) 
                        aulas_avulsas_restantes -= 1      
                        break                             

        if len(turma.horarios_alocados) < turma.aulas_semanais:
            turma.horarios_alocados.clear()
            turmas_com_erro.append(turma) 

    return turmas_com_erro