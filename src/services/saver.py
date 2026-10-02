"""
Encontra salas disponíveis para as turmas que já receberam horários e salva os cruzamentos no banco.
"""

import sqlite3

#Vincula salas aos horários e salvar no banco.
def alocar_salas(db_path, grafo, ordem_alocacao):
    #Conecta ao banco de dados.
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    #Busca todas as salas cadastradas.
    cursor.execute("SELECT sal_id, sal_bloco, sal_numero FROM sal_sala ORDER BY sal_id") 
    salas_disponiveis = cursor.fetchall()
    
    #Exclui os registros anteriores da tabela.
    cursor.execute("DELETE FROM alo_alocacaoHorarioSala")
    
    #Busca qual o maior ID atual na tabela de alocação para não haver duplicidade de chave primária.
    cursor.execute("SELECT MAX(alo_id) FROM alo_alocacaoHorarioSala")
    max_id = cursor.fetchone()[0] #Extrai o maior ID encontrado
    next_id = (max_id or 0) + 1 #Define o próximo ID a ser usado.
    
    ocupacao_salas = {}  #Dicionário para controlar salas usadas e seus horários.
    turmas_sem_sala = [] #Lista para registrar turmas que não encontraram sala.
    
    #Percorre as turmas.
    for tur_id in ordem_alocacao:
        turma = grafo.vertice_turmas[tur_id] #Pega a turma atual.
        
        #Pula se a turma não teve horários alocados.
        if not turma.horarios_alocados:
            continue
            
        sala_escolhida = None
        
        #Tenta achar uma sala livre nos horários daquela turma.
        for sala in salas_disponiveis:
            sal_id = sala[0]       #Pega o ID da sala atual.
            sala_livre = True      #Assume que está livre.
            
            #Testa todos os horários da turma para essa sala.
            for h in turma.horarios_alocados:
                #Se o ID da sala já está na lista de ocupados daquele horário.
                if sal_id in ocupacao_salas.get(h, []):
                    sala_livre = False 
                    break               
                    
            #Se a sala está livre.
            if sala_livre:
                sala_escolhida = sal_id
                break                  
                
        #Se encontrou uma sala viável para a turma
        if sala_escolhida:
            #Associa a sala escolhida para cada horário da turma
            for h in turma.horarios_alocados:
                #Se o horário não tem registros de sala, cria a lista vazia.
                if h not in ocupacao_salas:
                    ocupacao_salas[h] = []
                #Adiciona a sala na lista de ocupados daquele horário.
                ocupacao_salas[h].append(sala_escolhida)
                
                #Alocação de Turma + Sala + Horário no banco.
                cursor.execute(
                    "INSERT INTO alo_alocacaoHorarioSala (alo_id, idtur_turma, idsal_sala, idhor_horario) VALUES (?, ?, ?, ?)",
                    (next_id, tur_id, sala_escolhida, h)
                )
                next_id += 1 #Incrementa o ID da chave primária.
        #Registra que a turma ficou sem sala (sem sala viável).
        else:
            #Registra que a turma ficou sem sala.
            turmas_sem_sala.append(turma)
            

    conn.commit()
    conn.close()
    
    #Retorna as turmas que falharam em conseguir sala
    return turmas_sem_sala