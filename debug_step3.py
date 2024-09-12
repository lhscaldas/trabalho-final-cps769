from auxiliary_functions import *
from step_3 import FlagAndParams, step_3_process_with_flags

# Pergunta 1: Qual o bitrate médio dentro de cada rajada para o cliente rj e o servidor pi no período entre as 08 e 09h do dia 07/06/2024?
question_1 = FlagAndParams(
    unrelated_to_db=False,
    bitrate_burts=True,
    latency_match=False,
    worst_qoe_client=False,
    server_qoe_consistency=False,
    server_change_strategy=False,
    qoe_change=False,
    datahora_inicio='2024-06-07 08:00:00',
    datahora_final='2024-06-07 09:00:00',
    client='rj',
    server='pi', 
    bitrate_delta=0,
    latency_delta=0
)

# Pergunta 2: Qual a latência nas medições que coincidem com a janela de tempo das rajadas de medição de bitrate para o cliente rj e o servidor pi no período entre as 08 e 09h do dia 07/06/2024?
question_2 = FlagAndParams(
    unrelated_to_db=False,
    bitrate_burts=False,
    latency_match=True,
    worst_qoe_client=False,
    server_qoe_consistency=False,
    server_change_strategy=False,
    qoe_change=False,
    datahora_inicio='2024-06-07 08:00:00',
    datahora_final='2024-06-07 09:00:00',
    client='rj',
    server='pi', 
    bitrate_delta=0,
    latency_delta=0
)

# Pergunta 3: Qual cliente tem a pior qualidade de recepção de vídeo ao longo do tempo?
question_3 = FlagAndParams(
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
question_4 = FlagAndParams(
    qoe_required=True,
    latency_increase=False,
    server_variance=True,
    bitrate_average=False,
    latency_for_bursts=False,
    unrelated_to_db=False,
    client_specific='rj',
    server_specific="",
    # datahora_inicio='2024-06-07 00:00:00',
    # datahora_final='2024-06-10 23:59:59'
    datahora_inicio='2024-06-07 08:00:00',
    datahora_final='2024-06-07 09:00:00'
)


# Pergunta 5: Qual é a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente rj entre 07/06/2024 e 10/06/2024?
question_5 = FlagAndParams(
    qoe_required=True,
    latency_increase=False,
    server_variance=False,
    bitrate_average=False,
    latency_for_bursts=False,
    unrelated_to_db=False,
    client_specific='rj',
    server_specific="",
    # datahora_inicio='2024-06-07 00:00:00',
    # datahora_final='2024-06-10 23:59:59'
    datahora_inicio='2024-06-07 08:00:00',
    datahora_final='2024-06-07 09:00:00'
)

# Pergunta 6: Se a latência aumentar 20%, como isso afeta a QoE do cliente rj e servidor pi entre 07/06/2024 e 10/06/2024?
question_6 = FlagAndParams(
    qoe_required=True,
    latency_increase=True,
    server_variance=False,
    bitrate_average=False,
    latency_for_bursts=False,
    unrelated_to_db=False,
    client_specific='rj',
    server_specific='pi',
    # datahora_inicio='2024-06-07 00:00:00',
    # datahora_final='2024-06-10 23:59:59'
    datahora_inicio='2024-06-07 08:00:00',
    datahora_final='2024-06-07 09:00:00'
)

if __name__ == "__main__":
    processed_data = step_3_process_with_flags(question_1)
    processed_df = pd.DataFrame(processed_data)
    print(f"Resultado do processamento: \n{processed_df}")
    processed_data = step_3_process_with_flags(question_2)
    processed_df = pd.DataFrame(processed_data)
    print(f"Resultado do processamento: \n{processed_df}")
    


