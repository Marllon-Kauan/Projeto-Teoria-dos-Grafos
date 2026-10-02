"""
Cria o arquivo do banco de dados SQLite e o inicia.
"""

import sqlite3
import os

#Inicia e popula o banco.
def inicializar_banco():
    db_path = 'banco_projeto.db'
    sql_path = os.path.join('database', 'carga_de_dados.sql')
    
    #Conecta ao banco de dados SQLite.
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        script_sql = f.read()
        
    cursor.executescript(script_sql) #Executa os comandos SQL.
    conn.commit()
    conn.close()