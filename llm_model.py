from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from auxiliary_functions import *

import os
from env import OPENAI_API_KEY

# Configuração da chave de API
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Inicialização do modelo de linguagem
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
    )

class LogicalSteps(BaseModel):
    """Estrutura para os passos lógicos necessários."""
    steps: str = Field(description="Passos lógicos necessários para responder à pergunta")

def step_1_comprehend_question(question):
    """Modelo 1: Compreensão da Pergunta"""
    system_prompt_1 = """
        You are an AI that understands questions related to network measurements stored in SQL tables. Your task is to comprehend the user's question, analyze it in the context of the database structure, and produce the logical steps needed to calculate the appropriate results or generate flags in a follow-up process.

        **Database Context:**
        - The 'bitrate_train' table stores bitrate data, which is measured in bursts (groups of measurements with timestamps within 5 seconds).
        - The 'rtt_train' table stores latency (rtt) data, measured continuously but at irregular intervals.
        - Both tables include timestamps in Unix format, which can be used to match entries between them.
        - Available clients: 'ba', 'rj'; available servers: 'ce', 'df', 'es', 'pi'.

        **Types of Questions:**
        1. **Questions Unrelated to the Database:**
        - If the question does not involve the network measurement data (e.g., IP addresses, geography, general knowledge), classify it as unrelated to the database.
        
        2. **Questions Requiring Specific SQL Calculations or Queries:**
        - Identify logical steps for questions about network quality (QoE), burst averages, or matching latency with bitrate bursts, using both tables' data.
        - Questions may require generating flags such as for calculating burst averages, matching latencies, simulating QoE changes, or filtering by specific clients, servers, or time ranges.

        **Your Role:**
        - Break down the question into logical steps that help determine which calculations are needed.
        - If a question specifies a client, server, or time range, include these details in the logical steps.
        - Ensure that steps are detailed enough for the next stage, where flags will be generated for different scenarios like calculating averages, identifying QoE, or determining consistency over time.

        **Examples:**

        User: "Qual cliente tem a pior qualidade de recepção de vídeo ao longo do tempo?"
        Logical Steps:
        1. Calculate QoE for each client using 'bitrate_train' and 'rtt_train'.
        2. Ensure that QoE is only calculated when latency matches a burst of bitrate.
        3. Normalize both the bitrate and latency.
        4. Calculate QoE for each client over time.
        5. Identify the client with the lowest average QoE.

        User: "Qual servidor fornece a QoE mais consistente?"
        Logical Steps:
        1. Calculate QoE for each server using 'bitrate_train' and 'rtt_train'.
        2. Ensure QoE is only calculated when latency matches a burst of bitrate.
        3. Calculate the variance of QoE for each server.
        4. Identify the server with the lowest variance.

        User: "Qual é a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente ba?"
        Logical Steps:
        1. Identify all servers that client ba is connected to from 'bitrate_train' and 'rtt_train'.
        2. Calculate the QoE for each server over time.
        3. Determine the best server at each timestamp to maximize QoE for the client.
        4. Recommend the best server switching strategy based on QoE.

        User: "Se a latência aumentar 20%, como isso afeta a QoE do cliente rj?"
        Logical Steps:
        1. Retrieve current latency values for client rj from 'rtt_train'.
        2. Increase the latency values by 20%.
        3. Recalculate QoE using the modified latency values.
        4. Compare the new QoE values to the original ones and explain the impact of the latency change.

        User: "Qual o bitrate médio dentro de cada rajada para o cliente ba e o servidor pi no período entre 2024-06-07 e 2024-06-10?"
        Logical Steps:
        1. Filter 'bitrate_train' for client ba and server pi within the given time period.
        2. Group measurements into bursts (timestamps within 5 seconds of each other).
        3. Calculate the average bitrate for each burst.

        User: "Qual a latência nas medições que coincidem com as rajadas de bitrate para o cliente rj e o servidor df entre 2024-06-07 e 2024-06-10?"
        Logical Steps:
        1. Filter 'bitrate_train' for client rj and server df within the time period.
        2. Group measurements into bursts (timestamps within 5 seconds of each other).
        3. Match latency from 'rtt_train' within these burst windows.
        4. Return matching latency values.

        User: "Qual o IP do cliente rj na rede?"
        Logical Steps:
        1. Recognize that this question is unrelated to the available network measurement data.
        
        User: "Qual é a mediana da latência em uma janela de 1 minuto?"
        Logical Steps:
        1. The question requests a specific type of analysis not covered by the database schema.
        2. Inform the user that custom logic is required to answer this question.
        """

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_1), ("human", "{input}")])
    logical_steps_llm = prompt | llm.with_structured_output(LogicalSteps)
    logical_steps = logical_steps_llm.invoke(question)
    return logical_steps

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

def step_2_generate_flags(logical_steps):
    """Step 2: Geração de Flags com base nos passos lógicos"""

    system_prompt_2 = """
    You are an AI that generates flags based on logical steps describing the actions needed to answer a user's question related to network measurement data stored in SQL tables.

    Given the logical steps, generate flags to indicate the required calculations or to handle specific situations:
    
    - Set 'unrelated_to_db' to True if the question is not directly related to the available network measurement data in the database (e.g., IP addresses, network topology, or general knowledge like weather or geography).
    - Set 'bitrate_burts' to True if the question involves calculating the average bitrate within bursts.
    - Set 'latency_match' to True if the question asks for latency values that match burst intervals from the 'bitrate_train' table.
    - Set 'worst_qoe_client' to True if the question requires identifying the client with the worst Quality of Experience (QoE) (i.e. to find the client with the worst video reception quality over time).
    - Set 'server_qoe_consistency' to True if the question asks for the consistency of QoE for a client across servers.
    - Set 'server_change_strategy' to True if the question involves determining the best server switching strategy to maximize QoE.
    - Set 'qoe_change' to True if the question involves simulating a change in QoE with variations in bitrate or latency.
    - Set 'client' and 'server' to the names of the client and server if the question specifies them; otherwise, keep them as an empty string.
    - Set 'datahora_inicio' and 'datahora_final' to the start and end timestamps if the question specifies a time range, formatted as 'YYYY-MM-DD HH:MM:SS'; otherwise, keep them as the default values.
    - Set 'bitrate_delta' and 'latency_delta' to the specified variations in bitrate and latency if the question involves simulating these changes; otherwise, keep them as 0.

    **Important Clarifications:**
    - If the question is not about bitrate, latency, or Quality of Experience (QoE), it should be marked as 'unrelated_to_db'.
    - Any question involving specific clients (ba, rj), servers (ce, df, es, pi), or time ranges should have the appropriate flags filled accordingly.

    **Examples**:

    User: "Qual cliente tem a pior qualidade de recepção de vídeo ao longo do tempo?"
    Logical Steps:
    1. Calculate QoE for each client using bitrate from 'bitrate_train' and latency (RTT) from 'rtt_train'.
    2. Normalize both the bitrate and latency.
    3. Ensure that the QoE is only calculated when the latency coincides with a burst of bitrate.
    4. Calculate QoE for each client over time.
    5. Identify the client with the lowest average QoE.
    Flags: worst_qoe_client = True

    User: "Qual servidor fornece a QoE mais consistente?"
    Logical Steps:
    1. Calculate QoE for each server based on clients connected to it, using the 'bitrate_train' and 'rtt_train' tables.
    2. Normalize both the bitrate and latency.
    3. Ensure that QoE is only calculated when the latency coincides with a burst of bitrate.
    4. Calculate the variance of QoE for each server.
    5. Identify the server with the lowest variance in QoE.
    Flags: server_qoe_consistency = True

    User: "Qual é a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente ba?"
    Logical Steps:
    1. Identify all servers that the client is connected to from the 'bitrate_train' and 'rtt_train' tables.
    2. Calculate the QoE for each server over time.
    3. Determine the best server at each timestamp to maximize QoE for the client.
    4. Recommend the best server switching strategy based on QoE.
    Flags: server_change_strategy = True, client = 'ba'

    User: "Se a latência aumentar 20%, como isso afeta a QoE do cliente rj?"
    Logical Steps:
    1. Select the client and retrieve their current latency values from 'rtt_train'.
    2. Increase the latency values by 20%.
    3. Recalculate QoE using the modified latency values.
    4. Compare the new QoE values to the original and explain the impact of the latency change.
    Flags: qoe_change = True, client = 'rj', latency_delta = 20

    User: "Qual o bitrate médio dentro de cada rajada para o cliente ba e o servidor pi no período entre 2024-06-07 00:00:00 e 2024-06-10 23:59:59?"
    Logical Steps:
    1. Filter the 'bitrate_train' table for measurements related to client ba and server pi within the time period.
    2. Identify bursts by grouping measurements that occur within 5 seconds of each other.
    3. Calculate the average bitrate for each identified burst.
    Flags: bitrate_burts = True, client = 'ba', server = 'pi', datahora_inicio = '2024-06-07 00:00:00', datahora_final = '2024-06-10 23:59:59'

    User: "Qual a latência nas medições que coincidem com a janela de tempo das rajadas de medição de bitrate para o cliente rj e o servidor df no período entre 2024-06-07 00:00:00 e 2024-06-10 23:59:59?"
    Logical Steps:
    1. Filter the 'bitrate_train' table for measurements related to client rj and server df within the time period.
    2. Identify bursts by grouping measurements that occur within 5 seconds of each other.
    3. Find the corresponding latency measurements in the 'rtt_train' table that fall within the same time intervals as the bursts.
    4. Return these latency measurements.
    Flags: latency_match = True, client = 'rj', server = 'df', datahora_inicio = '2024-06-07 00:00:00', datahora_final = '2024-06-10 23:59:59'

    User: "Qual o IP do cliente rj na rede?"
    Logical Steps:
    1. This question is unrelated to the available network measurement data and involves general knowledge (e.g., weather, geography, IP addresses, or client-server network topology).
    Flags: unrelated_to_db = True

    User: "Qual é a mediana da latência em uma janela de 1 minuto?"
    Logical Steps:
    1. The user is asking for a specific type of analysis that is related to the network measurements but is not covered by any predefined examples.
    2. Inform the user that custom logic may be required to handle this specific question.
    Flags: unrelated_to_db = True
"""

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_2), ("human", "{logical_steps}")])
    flag_llm = prompt | llm.with_structured_output(FlagAndParams)
    flags = flag_llm.invoke(logical_steps)
    return flags

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

class NaturalLanguageResponse(BaseModel):
    """Estrutura para a resposta em linguagem natural"""
    response: str = Field(description="Natural language response to the user's query")

def step_4_generate_response(processed_data):
    """Step 4: Geração de Resposta em Linguagem Natural"""
    system_prompt_4 = """
        You are an AI tasked with generating a natural language response based on the processed data. Use the processed data to generate a coherent response.

        Processed Data:
        {processed_data}
    """
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_4), ("human", "{processed_data}")])
    response_llm = prompt | llm.with_structured_output(NaturalLanguageResponse)
    response = response_llm.invoke(processed_data)
    return response

def responder_pergunta(pergunta):
    """Função principal que executa todo o encadeamento para responder a pergunta do usuário."""
    
    # 1. Compreensão da Pergunta
    print("Step 1: Compreendendo a pergunta...")
    passos_logicos = step_1_comprehend_question(pergunta)
    
    # 2. Geração de Flags
    print("Step 2: Gerando flags...")
    flags = step_2_generate_flags(passos_logicos.steps)
    
    # 4. Processamento dos Dados com base nas flags
    print("Step 3: Processando os dados com base nas flags...")
    dados_processados = step_3_process_with_flags(flags)
    
    # 5. Geração de Resposta em Linguagem Natural
    print("Step 4: Gerando a resposta em linguagem natural...")
    resposta_final = step_4_generate_response(dados_processados)
    
    return resposta_final.response


