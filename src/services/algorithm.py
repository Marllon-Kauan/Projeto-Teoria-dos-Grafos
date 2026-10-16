"""
Ordena a prioridade das turmas e encaixa os horários duplos ou avulsos sem gerar conflitos.
"""

from collections import deque

#Maior quantidade de aulas seguidas no mesmo dia entre os horários informados.
#Os IDs seguem a mesma lógica dos blocos geminados abaixo: 6 horários por dia (1-6 segunda, 7-12 terça...).
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
        #Se a turma não foi visitada ainda, inicia uma busca em largura a partir dela.
        if tur_id_inicial not in visitados:
            fila = deque([tur_id_inicial]) #Coloca o ID inicial na fila.
            
            while fila: #Enquanto houver elementos na fila.
                atual = fila.popleft() 
                
                if atual not in visitados: #Se ainda não foi processado.
                    visitados.add(atual)           #Marca como processado.
                    ordem_alocacao.append(atual)   #Adiciona na ordem de saída.
                    
                    vizinhos = list(grafo.adjacencias.get(atual, {}).keys()) #Extrai a lista das turmas conflitantes.
                    
                    #Ordena os vizinhos pela quantidade de conflitos.
                    vizinhos_ordenados = sorted(
                        vizinhos,
                        key=lambda v_id: grafo.obter_grau(v_id),
                        reverse=True
                    )
                    
                    #Adiciona os vizinhos na fila (caso ainda não tenham sido visitados).
                    for vizinho in vizinhos_ordenados:
                        if vizinho not in visitados:
                            fila.append(vizinho)
                            
    return ordem_alocacao #Retorna a lista final com a ordem das turmas.


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

    turmas_com_erro = [] #Guarda as turmas que não couberam.

    #Processa as turmas.
    for tur_id in ordem_alocacao:
        turma = grafo.vertice_turmas[tur_id] 
        
        
        blocos_necessarios = turma.aulas_semanais // 2 #Calcula quantos blocos duplos a turma precisa ter.
        aulas_avulsas_restantes = turma.aulas_semanais % 2 #Identifica se sobra uma aula solta.
        blocos_alocados = 0 #Contador de quantos blocos já foram resolvidos.
        
        #Percorre a lista de blocos geminados disponíveis.
        for bloco in blocos_geminados:
            if blocos_alocados >= blocos_necessarios:
                break
                
            h1, h2 = bloco #Desempacota o par de horários do bloco
            
            #Verifica se os dois horários estão disponíveis nas regras da turma.
            if h1 not in turma.dominio_horarios or h2 not in turma.dominio_horarios:
                continue

            #Se o professor limitou aulas seguidas no dia, ignora o bloco que ultrapassa o limite.
            if turma.max_seguidas and maior_sequencia_no_dia(turma.horarios_alocados + [h1, h2]) > turma.max_seguidas:
                continue

            conflito = False
            #Checa todos os vizinhos conflitantes dessa turma.
            for vizinho_id in grafo.adjacencias.get(tur_id, {}):
                vizinho = grafo.vertice_turmas[vizinho_id]
                #Se o vizinho já ocupou algum dos dois horários, há conflito.
                if h1 in vizinho.horarios_alocados or h2 in vizinho.horarios_alocados:
                    conflito = True
                    break
                    
            #Se nenhum vizinho possui esse horário.
            if not conflito:
                #A turma adquire esses dois horários.
                turma.horarios_alocados.extend([h1, h2])
                blocos_alocados += 1 
                
        #Lida com aulas ímpares que sobraram.
        if aulas_avulsas_restantes > 0:
            #Procura um horário unitário dentre os horários viáveis da turma.
            for h in turma.dominio_horarios:
                #Verifica se a turma já não está ocupando esse horário.
                if h not in turma.horarios_alocados:
                    #Mesmo limite de aulas seguidas para a aula avulsa.
                    if turma.max_seguidas and maior_sequencia_no_dia(turma.horarios_alocados + [h]) > turma.max_seguidas:
                        continue
                    conflito = False
                    #Checa todos os vizinhos conflitantes da turma.
                    for vizinho_id in grafo.adjacencias.get(tur_id, {}):
                        vizinho = grafo.vertice_turmas[vizinho_id]
                        #Se o vizinho já usa esse horário.
                        if h in vizinho.horarios_alocados:
                            conflito = True
                            break
                    #Se encontrou um espaço livre.
                    if not conflito:
                        turma.horarios_alocados.append(h) 
                        aulas_avulsas_restantes -= 1      
                        break                             

        #Checa se no fim a turma conseguiu todas as aulas que precisa.
        if len(turma.horarios_alocados) < turma.aulas_semanais:
            turma.horarios_alocados.clear() #Remove os horários parciais salvos
            turmas_com_erro.append(turma) 

    #Retorna a lista de turmas problemáticas.
    return turmas_com_erro