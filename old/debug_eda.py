import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def carregar_dados(db_name, tabela_nome):
    """Carrega dados de uma tabela específica do banco de dados SQLite."""
    conn = sqlite3.connect(db_name)
    df = pd.read_sql(f'SELECT * FROM {tabela_nome}', conn)
    conn.close()
    return df

def converter_timestamp(df):
    """Converte a coluna de timestamp para datetime em UTC."""
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).dt.tz_convert('America/Sao_Paulo')
    return df

def filtrar_intervalo(df, inicio, fim):
    """
    Filtra os dados entre um intervalo de tempo específico.

    Parâmetros:
    - df: DataFrame com a coluna 'datetime'.
    - inicio: string ou datetime que define o início do intervalo (formato 'YYYY-MM-DD HH:MM').
    - fim: string ou datetime que define o fim do intervalo (formato 'YYYY-MM-DD HH:MM').

    Retorna:
    - DataFrame filtrado pelo intervalo de tempo especificado.
    """
    # Converter as strings de data/hora para objetos datetime, se necessário
    if isinstance(inicio, str):
        inicio = pd.to_datetime(inicio).tz_localize('America/Sao_Paulo')
    if isinstance(fim, str):
        fim = pd.to_datetime(fim).tz_localize('America/Sao_Paulo')

    # Certificar que a coluna 'datetime' está no fuso horário correto
    df['datetime'] = df['datetime'].dt.tz_convert('America/Sao_Paulo')

    # Filtragem dos dados entre as datas e horas especificadas
    df_filtered = df[(df['datetime'] >= inicio) & (df['datetime'] <= fim)]
    
    print(f"Número de linhas após a filtragem: {len(df_filtered)}")
    print(f"inicio = {inicio}, fim = {fim}")
    return df_filtered


if __name__ == "__main__":
    db_name = 'trabalho_raw.db'
    bitrate_df = carregar_dados(db_name, 'bitrate_train')
    rtt_df = carregar_dados(db_name, 'rtt_train')
    bitrate_df = converter_timestamp(bitrate_df)
    rtt_df = converter_timestamp(rtt_df)

    df_bitrate_filtrado = filtrar_intervalo(bitrate_df, inicio = '2024-06-07 08:00', fim = '2024-06-07 08:59' )
    print(df_bitrate_filtrado[(df_bitrate_filtrado['client'] == 'rj') & (df_bitrate_filtrado['server'] == 'pi')])
    df_rtt_filtrado = filtrar_intervalo(rtt_df, inicio = '2024-06-07 08:00', fim = '2024-06-07 08:59' )
    print(df_rtt_filtrado[(df_rtt_filtrado['client'] == 'rj') & (df_rtt_filtrado['server'] == 'pi')])