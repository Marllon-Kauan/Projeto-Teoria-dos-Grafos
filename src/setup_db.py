"""
Cria o arquivo do banco de dados SQLite e o inicializa.
"""

import sqlite3
import os

def inicializar_banco():
    #Obtém o diretório onde o setup_db.py está localizado
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    #Define os caminhos para o banco e o arquivo SQL.
    db_path = os.path.join(base_dir, 'banco_projeto.db')
    sql_path = os.path.join(base_dir, 'database', 'carga_de_dados.sql')
    
    #Se o banco já existir, remove para recriar do zero.
    if os.path.exists(db_path):
        os.remove(db_path)
    
    #Conecta ao banco de dados SQLite.
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    #Lê o script SQL.
    with open(sql_path, 'r', encoding='utf-8') as f:
        script_sql = f.read()
        
    cursor.executescript(script_sql) #Executa as instruções SQL.
    conn.commit()
    conn.close()
    
    print("Banco de dados criado e populado com sucesso!")

# Chama a função automaticamente ao executar o script pelo terminal
if __name__ == '__main__':
    inicializar_banco()