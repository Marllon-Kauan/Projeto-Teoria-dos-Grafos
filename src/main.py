"""
Executa o sistema.
"""

import sqlite3
import os
from database.connection import buscar_horarios
from services.builder import construir_grafo
from services.algorithm import ordenar_turmas, alocar_horarios
from services.saver import alocar_salas

#Função que exibe a grade horária.
def exibir_grade(db_path):
    conn = sqlite3.connect(db_path) #Conecta ao banco de dados.
    cursor = conn.cursor() #Cria um cursor para executar comandos SQL.
    
    #Define a consulta SQL para buscar os dados.
    query = """
    SELECT 
        HOR.hor_diaSemana,
        HOR.hor_horaInicio,
        HOR.hor_horaFim,
        DIS.dis_nome,
        PRO.pro_nome,
        SAL.sal_bloco, 
        SAL.sal_numero
    FROM alo_alocacaoHorarioSala ALO
    JOIN tur_turma TUR ON TUR.tur_id = ALO.idtur_turma
    JOIN dis_disciplina DIS ON DIS.dis_id = TUR.iddis_disciplina
    JOIN pro_professor PRO ON PRO.pro_id = TUR.idpro_professor
    JOIN sal_sala SAL ON SAL.sal_id = ALO.idsal_sala
    JOIN hor_horario HOR ON HOR.hor_id = ALO.idhor_horario
    ORDER BY HOR.hor_diaSemana, HOR.hor_horaInicio, SAL.sal_bloco, SAL.sal_numero;
    """
    
    #Executa a consulta.
    cursor.execute(query) 
    linhas = cursor.fetchall()
    conn.close()

    dias_semana = {
        2: "SEGUNDA-FEIRA", 3: "TERÇA-FEIRA", 
        4: "QUARTA-FEIRA", 5: "QUINTA-FEIRA", 6: "SEXTA-FEIRA"
    }
    
    print("\nGRADE HORÁRIA GERADA")

    dia_atual = None #Controla a mudança de dia.

    #Percorre cada linha de resultado do banco.
    for linha in linhas: 
        dia_num, inicio, fim, disciplina, professor, bloco, sala_num = linha
        
        #Verifica se o dia atual mudou.
        if dia_atual != dia_num:
            nome_dia = dias_semana.get(dia_num, f"DIA {dia_num}")
            print(f"\n{nome_dia}\n")
            dia_atual = dia_num
            
        h_inicio = f"{str(inicio).zfill(4)[:2]}:{str(inicio).zfill(4)[2:]}" #Hora do início.
        h_fim = f"{str(fim).zfill(4)[:2]}:{str(fim).zfill(4)[2:]}" #Hora do final.
        

        print(f"Disciplina: {disciplina}")
        print(f"Horário: {h_inicio} às {h_fim}")
        print(f"Professor: {professor}")
        print(f"Sala: {bloco}-{sala_num}\n")

#Função para capturar a entrada do usuário..
def obter_horarios_bloqueados(db_path):
    #Consulta os IDs de horários válidos no banco de dados.
    horarios_validos = set(buscar_horarios(db_path))
    
    print("Aviso: O bloqueio de horários aplica-se exclusivamente às turmas do 1º ao 4º período.")
    print("Digite os IDs dos horários que deseja bloquear separados por vírgula (Ex: 1, 2, 3).")
    print("Deixe em branco e aperte ENTER se não quiser bloquear nenhum horário.")
    entrada = input("IDs bloqueados: ")
    
    horarios = set()
    if not entrada.strip():
        return horarios
        
    for item in entrada.split(','):
        val = item.strip()
        if not val:
            continue
        try:
            hor_id = int(val)
            if hor_id in horarios_validos:
                horarios.add(hor_id)
            else:
                print(f"Aviso: O ID de horário '{hor_id}' não existe no banco de dados e foi ignorado.")
        except ValueError:
            print(f"Aviso: O valor '{val}' é inválido e foi ignorado.")
            
    return horarios


if __name__ == "__main__":
    #Localiza o banco.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(base_dir, "banco_projeto.db")
    
    SEMESTRE = 2
    
    #Captura os horários.
    horarios_bloqueados = obter_horarios_bloqueados(DB_PATH)
    print(f"\nHorários bloqueados definidos para o sistema: {horarios_bloqueados or 'Nenhum'}")

    #Constrói o grafo.
    grafo = construir_grafo(DB_PATH, SEMESTRE, horarios_bloqueados)
    ordem = ordenar_turmas(grafo) #Ordem de processamento das turmas.
    
    #Tenta alocar os horários primeiro
    turmas_sem_horario = alocar_horarios(grafo, ordem) 
    
    #Verifica se a grade foi possível
    if turmas_sem_horario:
        print("\nERRO: Não foi possível alocar horários para as seguintes turmas:")
        for turma in turmas_sem_horario:
            print(f"- Turma {turma.tur_codigo}: {turma.dis_nome} (Prof: {turma.pro_nome})") 
    else:
        #Só tenta alocar as salas e salvar no banco se todos os horários deram certo.
        turmas_sem_sala = alocar_salas(DB_PATH, grafo, ordem) 
        
        if turmas_sem_sala:
            print("\nERRO: Não há salas disponíveis suficientes para as seguintes turmas:")
            for turma in turmas_sem_sala:
                print(f"- Turma {turma.tur_codigo}: {turma.dis_nome} (Prof: {turma.pro_nome})")
        else:
            exibir_grade(DB_PATH)