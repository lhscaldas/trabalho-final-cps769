import numpy as np
import pandas as pd
import sqlite3
import time
from datetime import datetime

def aux_get_dataframes_from_db():
    """Função auxiliar para extrair as tabelas do banco de dados e convertê-las em dataframes"""
    
    # Caminho fixo para o banco de dados
    db_path = "trabalho_raw.db"
    
    # Estabelecer conexão com o banco de dados SQLite
    db_connection = sqlite3.connect(db_path)
    
    # Consultas para extrair as tabelas
    bitrate_query = "SELECT * FROM bitrate_train"
    rtt_query = "SELECT * FROM rtt_train"
    
    # Executa as queries e cria os dataframes
    bitrate_df = pd.read_sql(bitrate_query, db_connection)
    rtt_df = pd.read_sql(rtt_query, db_connection)
    
    # Fecha a conexão com o banco de dados
    db_connection.close()
    
    return bitrate_df, rtt_df

def aux_calcular_qoe(bitrate, rtt, min_bitrate, max_bitrate, min_rtt, max_rtt):
    """Função auxiliar para calcular a QoE"""
    bitrate_norm = (bitrate - min_bitrate) / (max_bitrate - min_bitrate)
    rtt_norm = (rtt - min_rtt) / (max_rtt - min_rtt)
    return bitrate_norm / rtt_norm if rtt_norm != 0 else 0

def aux_calcular_variancia_qoe(qoe_list):
    """Função auxiliar para calcular a variância da QoE"""
    return np.var(qoe_list)

def aux_simular_qoe_com_aumento_latencia(bitrate, rtt, aumento_percentual, min_bitrate, max_bitrate, min_rtt, max_rtt):
    """Função auxiliar para simular aumento de latência"""
    novo_rtt = rtt * (1 + aumento_percentual / 100)
    return aux_calcular_qoe(bitrate, novo_rtt, min_bitrate, max_bitrate, min_rtt, max_rtt)

def aux_calculate_bitrate_bursts(bitrate_df):
    """Função auxiliar para calcular o bitrate médio por rajada."""
    
    # Ordenar por timestamp
    bitrate_df = bitrate_df.sort_values(by='timestamp')
    
    bursts = []
    current_burst = []
    last_timestamp = None
    
    # Identificar as rajadas de medições
    for _, row in bitrate_df.iterrows():
        timestamp = row['timestamp']
        if last_timestamp is None or timestamp - last_timestamp <= 5:
            current_burst.append(row['bitrate'])
        else:
            # Quando a rajada termina, calcula a média do bitrate
            if current_burst:
                burst_average = sum(current_burst) / len(current_burst)
                bursts.append(burst_average)
            current_burst = [row['bitrate']]
        last_timestamp = timestamp
    
    # Para a última rajada
    if current_burst:
        burst_average = sum(current_burst) / len(current_burst)
        bursts.append(burst_average)
    
    return bursts

def aux_find_latency_for_bursts(bitrate_df, rtt_df):
    """Função auxiliar para encontrar a latência que coincide com as rajadas de bitrate."""
    
    # Ordenar os DataFrames por timestamp
    bitrate_df = bitrate_df.sort_values(by='timestamp')
    rtt_df = rtt_df.sort_values(by='timestamp')
    
    latency_for_bursts = []
    current_burst_timestamps = []
    last_timestamp = None
    
    # Identificar as rajadas de timestamps do bitrate
    for _, row in bitrate_df.iterrows():
        timestamp = row['timestamp']
        if last_timestamp is None or timestamp - last_timestamp <= 5:
            current_burst_timestamps.append(timestamp)
        else:
            if current_burst_timestamps:
                # Buscar as latências que coincidem com o intervalo da rajada
                burst_start = min(current_burst_timestamps)
                burst_end = max(current_burst_timestamps)
                latencies_in_burst = rtt_df[(rtt_df['timestamp'] >= burst_start) & (rtt_df['timestamp'] <= burst_end)]['rtt'].tolist()
                latency_for_bursts.append(latencies_in_burst)
            current_burst_timestamps = [timestamp]
        last_timestamp = timestamp
    
    # Para a última rajada de timestamps
    if current_burst_timestamps:
        burst_start = min(current_burst_timestamps)
        burst_end = max(current_burst_timestamps)
        latencies_in_burst = rtt_df[(rtt_df['timestamp'] >= burst_start) & (rtt_df['timestamp'] <= burst_end)]['rtt'].tolist()
        latency_for_bursts.append(latencies_in_burst)
    
    return latency_for_bursts

def aux_convert_datahora_to_timestamp(datahora_str):
    """Converte uma string de datahora (YYYY-MM-DD HH:MM:SS) para timestamp Unix."""
    dt = datetime.strptime(datahora_str, '%Y-%m-%d %H:%M:%S')
    timestamp = int(time.mktime(dt.timetuple()))
    return timestamp


