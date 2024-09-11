from auxiliary_functions import *
from llm_model import FlagOutput, step_3_process_with_flags
import pandas as pd

# Pergunta 1: Qual o bitrate médio dentro de cada rajada para o cliente rj e o servidor pi no período entre as 08 e 09h do dia 07/06/2024?
flags_1 = FlagOutput(
    qoe_required=False,
    latency_increase=False,
    server_variance=False,
    bitrate_average=True,
    latency_for_bursts=False,
    unrelated_to_db=False,
    client_specific='rj',
    server_specific='pi', 
    datahora_inicio='2024-06-07 08:00:00',
    datahora_final='2024-06-07 09:00:00'
)
def debug_question_1():
    processed_data = step_3_process_with_flags(flags_1)
    burts_df = processed_data['bitrate_bursts']
    
    # Convertendo as colunas timestamp
    burts_df['datahora_inicio'] = burts_df['timestamp_inicio'].apply(aux_convert_timestamp_to_datahora)
    burts_df['datahora_final'] = burts_df['timestamp_final'].apply(aux_convert_timestamp_to_datahora)
    burts_df = burts_df.drop(columns=['timestamp_inicio', 'timestamp_final'])
    
    print(f"Resultado do processamento: \n{burts_df}")

# Pergunta 2: Qual a latência nas medições que coincidem com a janela de tempo das rajadas de medição de bitrate para o cliente rj e o servidor pi no período entre as 08 e 09h do dia 07/06/2024?
flags_2 = FlagOutput(
    qoe_required=False,
    latency_increase=False,
    server_variance=False,
    bitrate_average=False,
    latency_for_bursts=True,
    unrelated_to_db=False,
    client_specific='rj',
    server_specific='pi',
    datahora_inicio='2024-06-07 08:00:00',
    datahora_final='2024-06-07 09:00:00'
)
def debug_question_2():
    processed_data = step_3_process_with_flags(flags_2)
    matched_df = processed_data['latency_for_bursts']
    
    # Convertendo as colunas timestamp
    matched_df['datahora'] = matched_df['timestamp'].apply(aux_convert_timestamp_to_datahora)
    matched_df = matched_df.drop(columns=['timestamp'])
    
    print(f"Resultado do processamento: \n{matched_df}")

# Pergunta 3: Qual cliente tem a pior qualidade de recepção de vídeo ao longo do tempo?
flags_3 = FlagOutput(
    qoe_required=True,
    latency_increase=False,
    server_variance=False,
    bitrate_average=False,
    latency_for_bursts=False,
    unrelated_to_db=False,
    client_specific="",
    server_specific="",
    datahora_inicio="",
    datahora_final=""
)

# Pergunta 4: Qual servidor fornece a QoE mais consistente para o cliente rj entre 07/06/2024 e 10/06/2024?
flags_4 = FlagOutput(
    qoe_required=True,
    latency_increase=False,
    server_variance=True,
    bitrate_average=False,
    latency_for_bursts=False,
    unrelated_to_db=False,
    client_specific='rj',
    server_specific="",
    datahora_inicio='2024-06-07 00:00:00',
    datahora_final='2024-06-10 23:59:59'
)

# Pergunta 5: Qual é a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente rj entre 07/06/2024 e 10/06/2024?
flags_5 = FlagOutput(
    qoe_required=True,
    latency_increase=False,
    server_variance=False,
    bitrate_average=False,
    latency_for_bursts=False,
    unrelated_to_db=False,
    client_specific='rj',
    server_specific="",
    datahora_inicio='2024-06-07 00:00:00',
    datahora_final='2024-06-10 23:59:59'
)

# Pergunta 6: Se a latência aumentar 20%, como isso afeta a QoE do cliente rj e servidor pi entre 07/06/2024 e 10/06/2024?
flags_6 = FlagOutput(
    qoe_required=True,
    latency_increase=True,
    server_variance=False,
    bitrate_average=False,
    latency_for_bursts=False,
    unrelated_to_db=False,
    client_specific='rj',
    server_specific='pi',
    datahora_inicio='2024-06-07 00:00:00',
    datahora_final='2024-06-10 23:59:59'
)


if __name__ == "__main__":
    debug_question_2()
    


