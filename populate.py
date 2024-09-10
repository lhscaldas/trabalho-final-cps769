import sqlite3
import pandas as pd
import os
from datetime import datetime

# Caminho da pasta onde o script .py está localizado
pasta_csv = os.path.dirname(os.path.abspath(__file__))

# Listar todos os arquivos CSV na pasta
csv_files = [f for f in os.listdir(pasta_csv) if f.endswith('.csv')]

# Verificar se há pelo menos 4 arquivos CSV na pasta
if len(csv_files) < 4:
    raise Exception("Existem menos de 4 arquivos CSV na pasta.")

# Pegar os primeiros 4 arquivos CSV
csv_files = csv_files[:4]

# Nome do banco de dados SQLite
db_name = 'trabalho_raw.db'

# Conectar ao banco de dados (ou criar se não existir)
conn = sqlite3.connect(db_name)

# Iterar sobre os arquivos CSV e inserir em tabelas com o mesmo nome dos arquivos
for file in csv_files:
    # Caminho completo do arquivo
    file_path = os.path.join(pasta_csv, file)
    
    # Ler o arquivo CSV
    df = pd.read_csv(file_path)
    
    # Garantir que as colunas sejam tratadas com os tipos corretos
    df['client'] = df['client'].astype(str)
    df['server'] = df['server'].astype(str)
    df['timestamp'] = df['timestamp'].astype(int)
    
    # Verificar e converter colunas opcionais
    if 'rtt' in df.columns:
        df['rtt'] = df['rtt'].astype(float)
    if 'bitrate' in df.columns:
        df['bitrate'] = df['bitrate'].astype(int)
    
    # Nome da tabela no banco de dados (remover a extensão .csv)
    table_name = os.path.splitext(file)[0]
    
    # Inserir o DataFrame no banco de dados
    df.to_sql(table_name, conn, if_exists='replace', index=False, dtype={
        'client': 'TEXT',
        'server': 'TEXT',
        'timestamp': 'INTEGER',
        'rtt': 'REAL',
        'bitrate': 'INTEGER',
    })

# Fechar a conexão com o banco de dados
conn.close()

print(f"Os arquivos CSV foram inseridos no banco de dados '{db_name}' com sucesso!")
