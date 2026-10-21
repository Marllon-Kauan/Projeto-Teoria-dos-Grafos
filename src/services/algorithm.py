"""
Ordena a prioridade das turmas e encaixa os horários duplos ou avulsos sem gerar conflitos,
utilizando um mapa dinâmico de horários extraído do banco de dados e distribuindo a carga pela semana.
"""

from collections import deque

#Cria um dicionário para busca rápida: id -> (dia, ordem)
def criar_mapa_horarios(horarios_do_banco):
    return {h['id']: (h['dia'], h.get('ordem', i)) for i, h in enumerate(horarios_do_banco)}

#Gera blocos duplos intercalando os dias da semana para evitar acúmulo no início da semana.
def gerar_blocos_geminados(horarios_do_banco):
    agrupados_por_dia = {}
    for h in horarios_do_banco:
        agrupados_por_dia.setdefault(h['dia'], []).append(h)
        
    blocos_por_dia = {}
    dias_ordem = []
    
    for dia, lista in agrupados_por_dia.items():
        if dia not in dias_ordem:
            dias_ordem.append(dia)
        lista_ordenada = sorted(lista, key=lambda x: x.get('ordem', x['id']))
        blocos_por_dia[dia] = []
        for i in range(0, len(lista_ordenada) - 1, 2):
            blocos_por_dia[dia].append((lista_ordenada[i]['id'], lista_ordenada[i+1]['id']))
            
    blocos = []
    max_blocos = max((len(b) for b in blocos_por_dia.values()), default=0)
    
    for i in range(max_blocos):
        for dia in dias_ordem:
            if i < len(blocos_por_dia[dia]):
                blocos.append(blocos_por_dia[dia][i])
                
    return blocos

#Pega todos os horários já alocados para todas as turmas do professor.
def horarios_do_professor(grafo, pro_id):
    horarios = []
    for turma in grafo.vertice_turmas.values():
        if turma.pro_id == pro_id:
            horarios.extend(turma.horarios_alocados)
    return horarios

#Conta quantas aulas existem em um dia específico.
def total_no_dia(mapa_horarios, alocacoes, dia_alvo):
    return sum(1 for h in alocacoes if mapa_horarios[h][0] == dia_alvo)

#Maior quantidade de aulas seguidas no mesmo dia entre os horários informados.
def maior_sequencia_no_dia(mapa_horarios, alocacoes):
    por_dia = {}
    for h in alocacoes:
        dia, ordem = mapa_horarios[h]
        por_dia.setdefault(dia, []).append(ordem)

    maior = 0
    for ordens in por_dia.values():
        ordens.sort()
        atual = 1 if ordens else 0
        for i in range(1, len(ordens)):
            if ordens[i] == ordens[i - 1] + 1:
                atual += 1
            else:
                atual = 1
            maior = max(maior, atual)
        maior = max(maior, atual)
    return maior

#Define em qual ordem as turmas devem ser resolvidas.
def ordenar_turmas(grafo):
    visitados = set()
    ordem_alocacao = []
    
    turmas_por_grau = sorted(
        grafo.vertice_turmas.keys(),
        key=lambda t_id: grafo.obter_grau(t_id),
        reverse=True
    )
    
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


def _tentar_alocar(turma, grafo, mapa_horarios, blocos_geminados, blocos_necessarios, aulas_avulsas, tentar_mesmo_dia):
    blocos_alocados = 0
    
    #Aloca os blocos duplos
    for h1, h2 in blocos_geminados:
        if blocos_alocados >= blocos_necessarios:
            break
            
        if h1 not in turma.dominio_horarios or h2 not in turma.dominio_horarios:
            continue
        if h1 in turma.horarios_alocados or h2 in turma.horarios_alocados:
            continue
            
        dia_h1 = mapa_horarios[h1][0]
        
        #Pula para o próximo dia se a turma já tem aula nesse dia
        if not tentar_mesmo_dia:
            if any(mapa_horarios[h][0] == dia_h1 for h in turma.horarios_alocados):
                continue

        horarios_prof = horarios_do_professor(grafo, turma.pro_id)

        if turma.max_seguidas and maior_sequencia_no_dia(mapa_horarios, horarios_prof + [h1, h2]) > turma.max_seguidas:
            continue
            
        if turma.max_diarias:
            if total_no_dia(mapa_horarios, horarios_prof + [h1, h2], dia_h1) > turma.max_diarias: 
                continue

        conflito = False
        for vizinho_id in grafo.adjacencias.get(turma.tur_id, {}):
            vizinho = grafo.vertice_turmas[vizinho_id]
            if h1 in vizinho.horarios_alocados or h2 in vizinho.horarios_alocados:
                conflito = True
                break
                
        if not conflito:
            turma.horarios_alocados.extend([h1, h2])
            blocos_alocados += 1 
            
    #Aloca as aulas avulsas.
    aulas_restantes = aulas_avulsas
    if aulas_restantes > 0:
        #Prioriza preencher horários cedo ao longo da semana.
        horarios_avulsos_ordenados = sorted(list(turma.dominio_horarios), key=lambda h: (mapa_horarios[h][1], mapa_horarios[h][0]))
        
        for h in horarios_avulsos_ordenados:
            if h not in turma.horarios_alocados:
                dia_h = mapa_horarios[h][0]
                
                if not tentar_mesmo_dia:
                    if any(mapa_horarios[ha][0] == dia_h for ha in turma.horarios_alocados):
                        continue

                horarios_prof = horarios_do_professor(grafo, turma.pro_id)

                if turma.max_seguidas and maior_sequencia_no_dia(mapa_horarios, horarios_prof + [h]) > turma.max_seguidas:
                    continue
                    
                if turma.max_diarias and total_no_dia(mapa_horarios, horarios_prof + [h], dia_h) > turma.max_diarias:
                    continue

                conflito = False
                for vizinho_id in grafo.adjacencias.get(turma.tur_id, {}):
                    vizinho = grafo.vertice_turmas[vizinho_id]
                    if h in vizinho.horarios_alocados:
                        conflito = True
                        break
                        
                if not conflito:
                    turma.horarios_alocados.append(h) 
                    aulas_restantes -= 1      
                    break


def alocar_horarios(grafo, ordem_alocacao, horarios_do_banco):
    mapa_horarios = criar_mapa_horarios(horarios_do_banco)
    blocos_geminados = gerar_blocos_geminados(horarios_do_banco)
    
    turmas_com_erro = []

    for tur_id in ordem_alocacao:
        turma = grafo.vertice_turmas[tur_id] 
        
        blocos_necessarios = turma.aulas_semanais // 2
        aulas_avulsas = turma.aulas_semanais % 2
        
        #Tenta forçar as aulas da disciplina a ficarem em dias separados.
        _tentar_alocar(turma, grafo, mapa_horarios, blocos_geminados, blocos_necessarios, aulas_avulsas, tentar_mesmo_dia=False)
        
        #Se a grade for muito restritiva e não conseguir espalhar, permite repetição de dias.
        if len(turma.horarios_alocados) < turma.aulas_semanais:
            turma.horarios_alocados.clear()
            _tentar_alocar(turma, grafo, mapa_horarios, blocos_geminados, blocos_necessarios, aulas_avulsas, tentar_mesmo_dia=True)

        #Se falhar nas duas tentativas, acusa erro para aquela turma.
        if len(turma.horarios_alocados) < turma.aulas_semanais:
            turma.horarios_alocados.clear()
            turmas_com_erro.append(turma) 

    return turmas_com_erro