import pandas as pd
pd.options.mode.copy_on_write = True
import sqlite3
import time
from datetime import datetime

def salvar_dataframes_em_txt(dataframes, arquivo_saida):
    """
    Salva uma lista de DataFrames em sequência em um arquivo de texto.
    
    Parâmetros:
    - dataframes: Lista de DataFrames a serem salvos.
    - arquivo_saida: Caminho do arquivo de saída.
    """
    with open(arquivo_saida, 'w') as f:
        for i, df in enumerate(dataframes):
            f.write(f"DataFrame {i+1}:\n")
            df.to_string(f)
            f.write("\n\n")  # Adiciona uma linha em branco entre os DataFrames

def salvar_variaveis_em_txt(variaveis, arquivo_saida):
    """
    Salva uma lista de variáveis em sequência em um arquivo de texto.
    
    Parâmetros:
    - variaveis: Lista de variáveis a serem salvas.
    - arquivo_saida: Caminho do arquivo de saída.
    """
    with open(arquivo_saida, 'w') as f:
        for i, var in enumerate(variaveis):
            f.write(f"Variável {i+1}:\n")
            f.write(str(var))
            f.write("\n\n")  # Adiciona uma linha em branco entre as variáveis

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

def aux_convert_datahora_to_timestamp(datahora_str):
    """Converte uma string de datahora (YYYY-MM-DD HH:MM:SS) para timestamp Unix."""
    dt = datetime.strptime(datahora_str, '%Y-%m-%d %H:%M:%S')
    timestamp = int(time.mktime(dt.timetuple()))
    return timestamp


def aux_convert_timestamp_to_datahora(timestamp):
    """
    Converte um timestamp (em segundos desde a época) para uma string de data e hora.
    """
    datahora = datetime.fromtimestamp(timestamp)
    return datahora.strftime('%Y-%m-%d %H:%M:%S')

def aux_filter_by_time(df, datahora_inicio, datahora_final):
    """
    Filtra um DataFrame para manter apenas as linhas que estão dentro de um intervalo de tempo.
    """
    if datahora_inicio != "2024-06-07 00:00:00" or datahora_final != "2024-06-10 23:59:59":
        timestamp_inicio = aux_convert_datahora_to_timestamp(datahora_inicio)
        timestamp_final = aux_convert_datahora_to_timestamp(datahora_final)     
        df = df[(df['timestamp'] >= timestamp_inicio) & (df['timestamp'] <= timestamp_final)]
        df = df.reset_index(drop=True)
    
    return df
    

def aux_calculate_bitrate_bursts(bitrate_df):
    """
    Função para calcular as rajadas de bitrate para cada combinação de cliente e servidor.
    Identifica intervalos de tempo em que as medições de bitrate ocorrem em sequência,
    separadas por no máximo 5 segundos, e calcula o bitrate médio dentro de cada rajada.
    """
    # Ordena o DataFrame por 'client', 'server' e 'timestamp' para garantir a ordem correta
    bitrate_df = bitrate_df.sort_values(by=['client', 'server', 'timestamp']).reset_index(drop=True)

    # Lista para armazenar todas as rajadas
    all_bursts = []

    # Agrupa o DataFrame por 'client' e 'server'
    grouped = bitrate_df.groupby(['client', 'server'])

    # Define o intervalo máximo de tempo entre medições para considerar uma continuação da rajada
    max_time_diff = 5  # em segundos

    for (client, server), group in grouped:
        # Calcula a diferença de tempo entre medições consecutivas
        group = group.copy()
        group['time_diff'] = group['timestamp'].diff()

        # Identifica o início de novas rajadas onde a diferença de tempo é maior que max_time_diff
        group['new_burst'] = (group['time_diff'] > max_time_diff) | (group['time_diff'].isnull())

        # Atribui um identificador único para cada rajada
        group['burst_id'] = group['new_burst'].cumsum()

        # Agrupa por 'burst_id' para calcular os detalhes de cada rajada
        bursts = group.groupby('burst_id').agg(
            client=('client', 'first'),
            server=('server', 'first'),
            timestamp_inicio=('timestamp', 'first'),
            timestamp_final=('timestamp', 'last'),
            bitrate_medio=('bitrate', 'mean')
        ).reset_index(drop=True)

        # Adiciona as rajadas do grupo atual à lista de todas as rajadas
        all_bursts.append(bursts)

    # Concatena todas as rajadas em um único DataFrame
    bursts_df = pd.concat(all_bursts, ignore_index=True)

    return bursts_df

def aux_find_latency_for_bursts(bursts_df, rtt_df):
    """
    Função para combinar medições de latência que coincidem com as rajadas de bitrate.
    Para cada par cliente x servidor, encontra as medidas de latência que coincidem com a janela de tempo da rajada.
    """
    
    # Definir uma lista para armazenar as medições que coincidem
    matched_df_list = []

    # Para cada rajada de bitrate, verificar quais medições de latência estão na mesma janela de tempo
    for _, burst in bursts_df.iterrows():
        # O início e o fim da rajada de bitrate
        burst_start = burst['timestamp_inicio']
        burst_end = burst['timestamp_final']
        cliente = burst['client']
        servidor = burst['server']

        # Filtrar as medições de latência que coincidem com essa rajada de bitrate e o par cliente-servidor
        matching_rtt = rtt_df[(rtt_df['timestamp'] >= burst_start - 150) & 
                              (rtt_df['timestamp'] <= burst_end + 150) & 
                              (rtt_df['client'] == cliente) & 
                              (rtt_df['server'] == servidor)]

        # Adicionar as medições encontradas para a lista
        if not matching_rtt.empty:
            matching_rtt['bitrate'] = burst['bitrate_medio']  # Associar o bitrate médio da rajada de bitrate
            # Calcular a média entre burst_start e burst_end
            avg_timestamp = (burst_start + burst_end) / 2
            matching_rtt['timestamp'] = avg_timestamp  # Atribuir a média ao timestamp
            matched_df_list.append(matching_rtt)

    # Reduzir os DataFrames com mais de uma linha a uma única linha calculando a média do RTT e do timestamp
    for i in range(len(matched_df_list)):
        if len(matched_df_list[i]) > 1:
            avg_rtt = matched_df_list[i]['rtt'].mean()
            
            # Manter apenas a primeira linha para preservar a estrutura
            matched_df_list[i] = matched_df_list[i].iloc[0:1]
            matched_df_list[i]['rtt'] = round(avg_rtt, 2)

    # Concatenar os DataFrames que coincidem
    if matched_df_list:
        matched_df = pd.concat(matched_df_list, ignore_index=True)
    else:
        matched_df = pd.DataFrame()  # Retornar DataFrame vazio se não houver correspondência    
    
    return matched_df

def aux_adicionar_normalizacao(matching_df):
    """
    Adiciona colunas de rtt_normalizado e bitrate_normalizado ao DataFrame,
    normalizando os valores para o DataFrame inteiro.
    """
    # Calcular os valores mínimos e máximos de bitrate e rtt para o DataFrame inteiro
    min_bitrate = matching_df['bitrate'].min()
    max_bitrate = matching_df['bitrate'].max()
    min_rtt = matching_df['rtt'].min()
    max_rtt = matching_df['rtt'].max()

    # Adicionar colunas normalizadas
    matching_df['bitrate_normalizado'] = (matching_df['bitrate'] - min_bitrate) / (max_bitrate - min_bitrate)
    matching_df['rtt_normalizado'] = (matching_df['rtt'] - min_rtt) / (max_rtt - min_rtt)

    return matching_df

def aux_calcular_qoe(bitrate_norm, rtt_norm):
    """Função auxiliar para calcular a QoE"""
    return bitrate_norm / rtt_norm if rtt_norm != 0 else bitrate_norm / 0.00001

def aux_simular_qoe_com_aumento_latencia(bitrate, rtt, aumento_percentual, min_bitrate, max_bitrate, min_rtt, max_rtt):
    """Função auxiliar para simular aumento de latência"""
    novo_rtt = rtt * (1 + aumento_percentual / 100)
    return aux_calcular_qoe(bitrate, novo_rtt, min_bitrate, max_bitrate, min_rtt, max_rtt)
































