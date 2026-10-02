"""
Executa o sistema.
"""

import sqlite3
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
    
    print("GRADE HORÁRIA GERADA")

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


if __name__ == "__main__":
    DB_PATH = "banco_projeto.db"
    SEMESTRE = 2
    horarios_bloqueados = {1, 2, 3, 4} #Restrição de horários bloqueados pelo usuário.

    #Constrói o grafo.
    grafo = construir_grafo(DB_PATH, SEMESTRE, horarios_bloqueados)
    ordem = ordenar_turmas(grafo) #Ordem de processamento das turmas.
    horarios = alocar_horarios(grafo, ordem) #Une os horários com as turmas.
    sala = alocar_salas(DB_PATH, grafo, ordem) #Une as salas.

    #Verificação de erros na alocação.
    if horarios or sala:
        print("Erro na alocação de turmas ou salas.")
    else:
        exibir_grade(DB_PATH)