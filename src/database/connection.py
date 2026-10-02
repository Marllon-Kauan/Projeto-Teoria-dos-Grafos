"""
Gerencia a comunicação com o banco de dados, executando as consultas SQL para extrair turmas e horários.
"""

import sqlite3

#Consulta SQL para buscar informações das turmas e disciplinas.
QUERY_TURMAS_SEMESTRE = """
SELECT 
    TUR.tur_id, 
    TUR.tur_codigo,
    DIS.dis_id, 
    DIS.dis_codigo, 
    DIS.dis_nome, 
    DIS.idper_periodo, 
    DIS.dis_cargaHoraria,
    PRO.pro_id, 
    PRO.pro_nome
FROM tur_turma TUR
JOIN dis_disciplina DIS ON DIS.dis_id = TUR.iddis_disciplina
JOIN pro_professor PRO ON PRO.pro_id = TUR.idpro_professor
WHERE TUR.idsem_semestre = ?;
"""

#Busca as turmas filtrando pelo ID do semestre.
def buscar_turmas(db_path, id_semestre):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(QUERY_TURMAS_SEMESTRE, (id_semestre,)) #Executa a consulta.
    rows = cursor.fetchall()
    conn.close()

    return rows

#Busca todos os IDs de horários.
def buscar_horarios(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT hor_id FROM hor_horario ORDER BY hor_id;") #Executa a consulta.
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]