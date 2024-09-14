from auxiliary_functions import *
from langchain_core.pydantic_v1 import BaseModel, Field

class FlagAndParams(BaseModel):
    """Estrutura para as flags geradas com base nos passos lógicos."""
    unrelated_to_db: bool = Field(default=False, description="Flag para indicar que a pergunta não está relacionada ao banco de dados")
    bitrate_burts: bool = Field(default=False, description="Flag para indicar se a média do bitrate por rajada deve estar na resposta")
    latency_match: bool = Field(default=False, description="Flag para indicar se a latência média por rajada deve estar na resposta")
    worst_qoe_client: bool = Field(default=False, description="Flag para indicar se o cliente com a pior QoE deve estar na resposta")
    server_qoe_consistency: bool = Field(default=False, description="Flag para indicar se a consistência da QoE por servidor deve estar na resposta")
    server_change_strategy: bool = Field(default=False, description="Flag para indicar se a estratégia de mudança de servidor deve estar na resposta")
    qoe_change: bool = Field(default=False, description="Flag para indicar se a mudança de QoE com a variação de bitrate ou de rtt deve estar na resposta")
    datahora_inicio: str = Field(default="2024-06-07 00:00:00", description="Data de início do intervalo de tempo")
    datahora_final: str = Field(default="2024-06-10 23:59:59", description="Data final do intervalo de tempo")
    client: str = Field(default="", description="Nome do cliente específico, se aplicável, ou False")
    server: str = Field(default="", description="Nome do servidor específico, se aplicável, ou False")
    bitrate_delta: int = Field(default=0, description="Variação de bitrate para considerar no calculo de um novo QoE")
    latency_delta: int = Field(default=0, description="Variação de latência para considerar no calculo de um novo QoE")


def step_3_process_with_flags(flags):
    """Step 3: Processa os dados com base nas flags geradas no step_2."""
    processed_data = {}

    # Verifica se a pergunta é considerada não relacionada ao banco de dados
    if flags.unrelated_to_db:
        processed_data['info'] = "A pergunta não está relacionada ao banco de dados disponível."
        # Encerra o processamento
        return processed_data

    # Extrai os DataFrames do banco de dados (essa função deve lidar com a extração dos dados)
    bitrate_df, rtt_df = aux_get_dataframes_from_db()

    # Aplica o filtro de tempo com base no timestamp, se necessário
    bitrate_df = aux_filter_by_time(bitrate_df, flags.datahora_inicio, flags.datahora_final)
    rtt_df = aux_filter_by_time(rtt_df, flags.datahora_inicio, flags.datahora_final)

    # Calcula o bitrate médio por rajada
    burts_df = aux_calculate_bitrate_bursts(bitrate_df)
    burts_df = burts_df.reset_index(drop=True)

    # Calcula a latência para as rajadas de bitrate
    matching_df = aux_find_latency_for_bursts(burts_df, rtt_df)
    matching_df = matching_df.reset_index(drop=True)

    # Flag para responder o bitrate médio por rajada
    if flags.bitrate_burts:
        df = burts_df.copy()

        if flags.client != "":
            df = df[df['client'] == flags.client ]
        if flags.server != "":
            df = df[df['server'] == flags.server ]

        df = df.reset_index(drop=True)

        processed_data['client'] = df['client']
        processed_data['server'] = df['server']
        processed_data['datahora_inicio'] = df['timestamp_inicio'].apply(aux_convert_timestamp_to_datahora)
        processed_data['datahora_final'] = df['timestamp_final'].apply(aux_convert_timestamp_to_datahora)
        processed_data['bitrate_bursts'] =  df['bitrate_medio']

    # Flag para responder a latência para as rajadas de bitrate
    elif flags.latency_match:
        df = matching_df.copy()

        if flags.client != "":
            df = df[df['client'] == flags.client ]
        if flags.server != "":
            df = df[df['server'] == flags.server ]

        df = df.reset_index(drop=True)

        processed_data['client'] = df['client']
        processed_data['server'] = df['server']
        processed_data['datahora'] = df['timestamp'].apply(aux_convert_timestamp_to_datahora)
        processed_data['latency'] =  df['rtt']
    
    # Flag para calcular a QoE e encontrar o pior cliente
    elif flags.worst_qoe_client:
        # Adicionar colunas normalizadas ao matching_df
        df = aux_adicionar_normalizacao(matching_df)

        if flags.server != "":
            df = df[df['server'] == flags.server ]
            df = df.reset_index(drop=True)

        # Calcular a QoE para cada linha do matching_df usando as colunas normalizadas
        df['QoE'] = df.apply(
            lambda row: aux_calcular_qoe(
                row['bitrate_normalizado'], 
                row['rtt_normalizado']
            ), 
            axis=1
        )

        # Calcular a QoE média por cliente
        qoe_by_client = df.groupby('client')['QoE'].mean().to_dict()

        # Encontrar o cliente com a pior QoE
        worst_client = min(qoe_by_client, key=qoe_by_client.get)

        processed_data['worst_client'] = worst_client
        processed_data['worst_client_mean_qoe'] = qoe_by_client[worst_client]

    # Flag para calcular a consistência da QoE por servidor
    elif flags.server_qoe_consistency:
        # Adicionar colunas normalizadas ao matching_df
        df = aux_adicionar_normalizacao(matching_df)

        # Filtrar por cliente
        if flags.client != "":
            df = df[df['client'] == flags.client ]
            df = df.reset_index(drop=True)

        # Calcular a QoE para cada linha do matching_df usando as colunas normalizadas
        df['QoE'] = df.apply(
            lambda row: aux_calcular_qoe(
                row['bitrate_normalizado'], 
                row['rtt_normalizado']
            ), 
            axis=1
        )

        # Calcular a variância da QoE por servidor
        variance_by_server = df.groupby('server')['QoE'].var().to_dict()

        processed_data['qoe_variance'] = variance_by_server
        min_key = min(variance_by_server, key=variance_by_server.get)
        min_value = variance_by_server[min_key]
        processed_data['best_qoe_variance'] = {min_key, min_value}

    # Flag para calcular a estratégia de mudança de servidor
    elif flags.server_change_strategy:
        # Adicionar colunas normalizadas ao matching_df
        df = aux_adicionar_normalizacao(matching_df)

        if flags.client != "":
            df = df[df['client'] == flags.client ]
            df = df.reset_index(drop=True)

        # Calcular a QoE para cada linha do matching_df usando as colunas normalizadas
        df['QoE'] = df.apply(
            lambda row: aux_calcular_qoe(
                row['bitrate_normalizado'], 
                row['rtt_normalizado']
            ), 
            axis=1
        )

        # Criar uma nova coluna que representa o início de cada janela de 10 segundos
        df['window_start'] = (df['timestamp'] // 10) * 10

        # Agrupar os dados por essa nova coluna e selecionar a linha com a maior QoE em cada grupo
        best_server_df = df.loc[df.groupby('window_start')['QoE'].idxmax()]

        # Resetar o índice do DataFrame resultante
        best_server_df.reset_index(drop=True, inplace=True)

        best_server_df['datahora'] = best_server_df['timestamp'].apply(aux_convert_timestamp_to_datahora)
        processed_data['server_change_strategy'] = best_server_df['server']
        processed_data['datahora'] = best_server_df['datahora']
        processed_data['QoE'] = best_server_df['QoE']

    elif flags.qoe_change:
        # Adicionar colunas normalizadas ao matching_df
        df_1 = aux_adicionar_normalizacao(matching_df)

        # Criar o dataframe modificado
        df_2 = matching_df.copy()
        df_2.loc[(df_2['client'] == flags.client) & (df_2['server'] == flags.server), 'bitrate'] *= (1 + flags.bitrate_delta / 100)
        df_2.loc[(df_2['client'] == flags.client) & (df_2['server'] == flags.server), 'rtt'] *= (1 + flags.latency_delta / 100)
        df_2 = aux_adicionar_normalizacao(df_2)

        # Filtrar por cliente e servidor
        if flags.client != "":
            df_1 = df_1[df_1['client'] == flags.client ]
            df_1 = df_1.reset_index(drop=True)
            df_2 = df_2[df_2['client'] == flags.client ]
            df_2 = df_2.reset_index(drop=True)
        if flags.server != "":
            df_1 = df_1[df_1['server'] == flags.server ]
            df_1 = df_1.reset_index(drop=True)
            df_2 = df_2[df_2['server'] == flags.server ]
            df_2 = df_2.reset_index(drop=True)


        # Calcular a QoE para cada linha dos dfs usando as colunas normalizadas
        df_1['QoE'] = df_1.apply(
            lambda row: aux_calcular_qoe(
                row['bitrate_normalizado'], 
                row['rtt_normalizado']
            ), 
            axis=1
        )

        df_2['QoE'] = df_2.apply(
            lambda row: aux_calcular_qoe(
                row['bitrate_normalizado'], 
                row['rtt_normalizado']
            ), 
            axis=1
        )

        # Juntar tudo em um df só
        df = df_1.copy()
        df['new_bitrate'] = df_2['bitrate']
        df['new_bitrate_normalizado'] = df_2['bitrate_normalizado']
        df['new_rtt'] = df_2['rtt']
        df['new_rtt_normalizado'] = df_2['rtt_normalizado']
        df['new_QoE'] = df_2['QoE']

        processed_data['QoE'] = df['QoE']
        processed_data['new_QoE'] = df['new_QoE']

    # Caso não entre em nenhum if, a pergunta não foi compreendida
    else:
        processed_data['info'] = "Pergunta não compreendida."    

    return processed_data, df

def old(flags):
    """Step 3: Processa os dados com base nas flags geradas no step_2."""
    processed_data = {}

    # Verifica se a pergunta é considerada não relacionada ao banco de dados
    if flags.unrelated_to_db:
        processed_data['info'] = "A pergunta não está relacionada ao banco de dados disponível."
        return processed_data

    # Extrai os DataFrames do banco de dados (essa função deve lidar com a extração dos dados)
    bitrate_df, rtt_df = aux_get_dataframes_from_db()

    # Aplica os filtros de cliente e/ou servidor, se necessário
    if flags.client_specific != "":
        bitrate_df = bitrate_df[bitrate_df['client'] == flags.client_specific]
        rtt_df = rtt_df[rtt_df['client'] == flags.client_specific]
    if flags.server_specific != "":
        bitrate_df = bitrate_df[bitrate_df['server'] == flags.server_specific]
        rtt_df = rtt_df[rtt_df['server'] == flags.server_specific]

    # Aplica o filtro de tempo com base no timestamp, se necessário
    if flags.datahora_inicio != "" and flags.datahora_final != "":
        timestamp_inicio = aux_convert_datahora_to_timestamp(flags.datahora_inicio)
        timestamp_final = aux_convert_datahora_to_timestamp(flags.datahora_final)
        bitrate_df = bitrate_df[(bitrate_df['timestamp'] >= timestamp_inicio) & (bitrate_df['timestamp'] <= timestamp_final)]
        rtt_df = rtt_df[(rtt_df['timestamp'] >= timestamp_inicio) & (rtt_df['timestamp'] <= timestamp_final)]

    # Calcula o bitrate médio por rajada
    burts_df = aux_calculate_bitrate_bursts(bitrate_df)

    # Calcula a latência para as rajadas de bitrate
    matching_df = aux_find_latency_for_bursts(burts_df, rtt_df)

    # Flag para responder o bitrate médio por rajada
    if flags.bitrate_average:
        processed_data['bitrate_bursts'] = burts_df

    # Flag para responder a latência para as rajadas de bitrate
    if flags.latency_for_bursts:
        processed_data['latency_for_bursts'] = matching_df

    # Flag para calcular a QoE apenas quando a latência coincidir com uma rajada de bitrate
    if flags.qoe_required:
        # Adicionar colunas normalizadas ao matching_df
        matching_df = aux_adicionar_normalizacao(matching_df)

        # Calcular a QoE para cada linha do matching_df usando as colunas normalizadas
        matching_df['QoE'] = matching_df.apply(
            lambda row: aux_calcular_qoe(
                row['bitrate_normalizado'], 
                row['rtt_normalizado']
            ), 
            axis=1
        )

        # A saída é o DataFrame com a coluna QoE adicionada
        processed_data['QoE'] = matching_df

    # Flag para calcular a variância da QoE por servidor
    if flags.server_variance:
        matching_df = processed_data['QoE']
        print(matching_df.groupby('server')['QoE'])
        variance_by_server = matching_df.groupby('server')['QoE'].var().to_dict()
        processed_data['QoE Variance'] = variance_by_server

    # Flag para simular aumento de latência
    if flags.latency_increase:       

        # Calcular a QoE para cada linha do matching_df usando as colunas normalizadas
        matching_df = aux_adicionar_normalizacao(matching_df)
        matching_df['QoE'] = matching_df.apply(
            lambda row: aux_calcular_qoe(
                row['bitrate_normalizado'], 
                row['rtt_normalizado']
            ), 
            axis=1
        )

        # Calcular a QoE novo para cada linha do matching_df
        matching_df_new = matching_df.copy()
        matching_df_new['rtt'] = matching_df_new['rtt'] * (1 + 20 / 100)
        matching_df_new = aux_adicionar_normalizacao(matching_df_new)
        matching_df['rtt_new'] = matching_df_new['rtt']
        matching_df['rtt_new_normalizado'] = matching_df_new['rtt_normalizado']
        matching_df['QoE_novo'] = matching_df.apply(
            lambda row: aux_calcular_qoe(
                row['bitrate_normalizado'], 
                row['rtt_new_normalizado']
            ), 
            axis=1
        )

        # A saída é o DataFrame com a coluna QoE adicionada
        processed_data['QoE_simulado'] = matching_df
            
    return processed_data