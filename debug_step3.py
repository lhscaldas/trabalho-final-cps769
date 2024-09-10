from auxiliary_functions import aux_get_dataframes_from_db
from llm_model import FlagOutput
import pandas as pd


# Pergunta 1: Qual cliente tem a pior qualidade de recepção de vídeo ao longo do tempo?
flags = FlagOutput(
    qoe_required=True,
    latency_increase=False,
    server_variance=False,
    bitrate_average=False,
    latency_for_bursts=False,
    unrelated_to_db=False,
    client_specific=False,
    server_specific=False,
    datahora_inicio=False,
    datahora_final=False
)
processed_data = {}
# Extrai os DataFrames do banco de dados (essa função deve lidar com a extração dos dados)
bitrate_df, rtt_df = aux_get_dataframes_from_db()

def aux_calcular_qoe(bitrate, rtt, min_bitrate, max_bitrate, min_rtt, max_rtt):
    """Função auxiliar para calcular a QoE"""
    bitrate_norm = (bitrate - min_bitrate) / (max_bitrate - min_bitrate)
    rtt_norm = (rtt - min_rtt) / (max_rtt - min_rtt)
    return bitrate_norm / rtt_norm if rtt_norm != 0 else 0

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

def aux_match_latency_with_bitrate_bursts(bursts_df, rtt_df):
    """
    Função para combinar medições de latência que coincidem com as rajadas de bitrate.
    """
    # Definir uma lista para armazenar as medições que coincidem
    matched_df_list = []

    # Para cada rajada de bitrate, verificar quais medições de latência estão na mesma janela de tempo
    for _, burst in bursts_df.iterrows():
        # O início e o fim da rajada de bitrate
        burst_start = burst['timestamp_inicio']
        burst_end = burst['timestamp_final']

        # Filtrar as medições de latência que coincidem com essa rajada de bitrate
        matching_rtt = rtt_df[(rtt_df['timestamp'] >= burst_start) & (rtt_df['timestamp'] <= burst_end)]

        # Adicionar as medições encontradas para a lista
        if not matching_rtt.empty:
            matching_rtt['bitrate'] = burst['bitrate_medio']  # Associar o bitrate médio da rajada de bitrate
            matched_df_list.append(matching_rtt)

    # Concatenar os DataFrames que coincidem
    if matched_df_list:
        matched_df = pd.concat(matched_df_list, ignore_index=True)
    else:
        matched_df = pd.DataFrame()  # Retornar DataFrame vazio se não houver correspondência

    return matched_df

# Flag para calcular a QoE
if flags.qoe_required:
        bursts = aux_calculate_bitrate_bursts(bitrate_df)  # Obtém as rajadas de bitrate
        # Verifica se os timestamps de latência coincidem com as rajadas de bitrate
        matching_df = aux_match_latency_with_bitrate_bursts(bursts, rtt_df)
        
        # Calcula os valores mínimos e máximos de bitrate e rtt
        min_bitrate = matching_df['bitrate'].min()
        max_bitrate = matching_df['bitrate'].max()
        min_rtt = matching_df['rtt'].min()
        max_rtt = matching_df['rtt'].max()

        # Calcula a QoE com base nos valores do próprio dataframe
        matching_df['QoE'] = matching_df.apply(lambda row: aux_calcular_qoe(row['bitrate'], row['rtt'], 
                                                                            min_bitrate=min_bitrate, 
                                                                            max_bitrate=max_bitrate, 
                                                                            min_rtt=min_rtt, 
                                                                            max_rtt=max_rtt), axis=1)
        qoe_by_client = matching_df.groupby('client')['QoE'].mean().to_dict()
        processed_data['QoE'] = qoe_by_client

print(processed_data)



