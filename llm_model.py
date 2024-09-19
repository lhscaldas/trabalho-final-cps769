from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from auxiliary_functions import *
import os

# Tente carregar a chave da API do arquivo env.py (apenas localmente)
try:
    from env import OPENAI_API_KEY
    print("Chave de API carregada do env.py.")
except ImportError:
    # Caso o arquivo env.py não exista, busque a chave das variáveis de ambiente (incluindo Secrets no Render)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        print(f"Chave de API carregada das variáveis de ambiente: {OPENAI_API_KEY[:4]}***")
    else:
        print("A variável OPENAI_API_KEY não foi encontrada nas variáveis de ambiente ou secrets.")

# Verificação para garantir que a chave foi carregada corretamente
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    print("API Key configurada com sucesso.")
else:
    raise EnvironmentError("A variável OPENAI_API_KEY não está definida!")


# Inicialização do modelo de linguagem
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1
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
    bitrate_bursts: bool = Field(default=False, description="Flag para indicar se a média do bitrate por rajada deve estar na resposta")
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
    - Set 'bitrate_bursts' to True if the question involves calculating the average bitrate within bursts.
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
    Flags: bitrate_bursts = True, client = 'ba', server = 'pi', datahora_inicio = '2024-06-07 00:00:00', datahora_final = '2024-06-10 23:59:59'

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

def step_3_process_with_flags(question, flags):
    """Step 3: Processa os dados com base nas flags geradas no step_2."""
    processed_data = {}
    processed_data['question'] = question
    df = pd.DataFrame()

    # Verifica se a pergunta é considerada não relacionada ao banco de dados
    if flags.unrelated_to_db:
        processed_data['info'] = "A pergunta não está relacionada ao banco de dados disponível."
        # Encerra o processamento
        return processed_data, df

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
    if flags.bitrate_bursts:
        df = burts_df.copy()

        if flags.client != "":
            df = df[df['client'] == flags.client ]
        if flags.server != "":
            df = df[df['server'] == flags.server ]

        df = df.reset_index(drop=True)

        processed_data['client'] = flags.client
        processed_data['server'] = flags.server
        df['datahora_inicio'] = df['timestamp_inicio'].apply(aux_convert_timestamp_to_datahora).to_json()
        df['datahora_final'] = df['timestamp_final'].apply(aux_convert_timestamp_to_datahora).to_json()
        processed_data['bitrate_bursts'] =  df[['datahora_inicio','datahora_final','bitrate_medio']].to_json()

    # Flag para responder a latência para as rajadas de bitrate
    elif flags.latency_match:
        df = matching_df.copy()

        if flags.client != "":
            df = df[df['client'] == flags.client ]
        if flags.server != "":
            df = df[df['server'] == flags.server ]

        df = df.reset_index(drop=True)

        processed_data['client'] = flags.client
        processed_data['server'] = flags.server
        df['datahora'] = df['timestamp'].apply(aux_convert_timestamp_to_datahora).to_json()
        processed_data['latency'] =  df[['datahora','bitrate','rtt']].to_json()
    
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
        processed_data['client'] = flags.client

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

        best_server_df['datahora'] = best_server_df['timestamp'].apply(aux_convert_timestamp_to_datahora).to_json()
        processed_data['server_change_strategy'] = best_server_df['server'].to_json()
        processed_data['datahora'] = best_server_df['datahora'].to_json()
        processed_data['QoE'] = best_server_df['QoE'].to_json()
        processed_data['client'] = flags.client

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

        processed_data['QoE'] = df['QoE'].to_json()
        processed_data['new_QoE'] = df['new_QoE'].to_json()

        processed_data['client'] = flags.client
        processed_data['server'] = flags.server
        processed_data['datahora'] = df['timestamp'].apply(aux_convert_timestamp_to_datahora).to_json()

    # Caso não entre em nenhum if, a pergunta não foi compreendida
    else:
        processed_data['info'] = "Pergunta não compreendida."    

    return processed_data, df


class NaturalLanguageResponse(BaseModel):
    """Estrutura para a resposta em linguagem natural"""
    response: str = Field(description="Natural language response to the user's query")

def step_4_generate_response(processed_data):
    # Extrair os dados do processed_data para passar ao template
    data = {
        'question': processed_data.get('question', 'Pergunta não fornecida'),
        'client': processed_data.get('client', 'Cliente não especificado'),
        'server': processed_data.get('server', 'Servidor não especificado'),
        'datahora_inicio': processed_data.get('datahora_inicio', 'Data de início não disponível'),
        'datahora_final': processed_data.get('datahora_final', 'Data de final não disponível'),
        'datahora': processed_data.get('datahora', 'Data não disponível'),
        'bitrate_bursts': processed_data.get('bitrate_bursts', 'Bitrate não disponível'),
        'latency': processed_data.get('latency', 'Latência não disponível'),
        'worst_client': processed_data.get('worst_client', 'Cliente não disponível'),
        'worst_client_mean_qoe': processed_data.get('worst_client_mean_qoe', 'QoE não disponível'),
        'QoE': processed_data.get('QoE', 'QoE não disponível'),
        'new_QoE': processed_data.get('new_QoE', 'QoE nova não disponível'),
        'qoe_variance': processed_data.get('qoe_variance', 'Variação da QoE não disponível'),
        'best_qoe_variance': processed_data.get('best_qoe_variance', 'Melhor QoE não disponível'),
        'server_change_strategy': processed_data.get('server_change_strategy', 'Estratégia de troca de servidor não disponível'),
        'info': processed_data.get('info', 'Informação não disponível'),
        'processed_data': processed_data
    }

    system_prompt_4 = """
        You are an AI tasked with generating a natural language response based on the processed data. Use the data to generate a coherent and contextually accurate response to the user's question.

        **Guidelines**:
        1. Always generate a response based on the data given. Ensure that all possible variables (e.g., 'QoE', 'worst_client', 'qoe_variance', 'bitrate_bursts', etc.) are referenced using placeholders like `{client}`, `{server}`, etc.
        2. If a variable is missing, assume it's not relevant to the question and skip it in the response.
        3. Always include the user's question in the final response by referencing `{question}`.

        **Response Examples**:

        User: "Qual o bitrate médio dentro de cada rajada para o cliente rj e o servidor pi no período entre as 08 e 09h do dia 07/06/2024?"
        Input Data: {datahora_inicio},  {bitrate_bursts}
        AI: Entre 08:00 e 09:00 do dia 07/06/2024, o bitrate médio dentro de cada rajada foi:
            - "datahora_inicio_1: bitrate_1 bps."
            - "datahora_inicio_2: bitrate_2 bps."
            - "datahora_inicio_3: bitrate_3 bps."
            ...

        User: "Qual a latência nas medições que coincidem com a janela de tempo das rajadas de medição de bitrate para o cliente rj e o servidor pi no período entre as 08 e 09h do dia 07/06/2024?"
        Input Data: {datahora}, {latency}
        AI: Entre 08:00 e 09:00 do dia 07/06/2024, as latências que coincidiram com as rajadas de bitrate foram as seguintes:
            - "datahora_1: latency_1 bps."
            - "datahora_2: latency_2 bps."
            - "datahora_3: latency_3 bps."
            ... 

        User: "Qual cliente tem a pior qualidade de recepção de vídeo entre as 08 e 09h do dia 07/06/2024?"
        AI: Entre 08:00 e 09:00 do dia 07/06/2024, o cliente com a pior qualidade de recepção de vídeo foi '{worst_client}', com uma média de QoE de {worst_client_mean_qoe}."

        User: "Qual servidor fornece a QoE mais consistente para o cliente rj entre as 08 e 09h do dia 07/06/2024?"
        AI: Entre 08:00 e 09:00 do dia 07/06/2024, o servidor '{qoe_variance}' forneceu a QoE mais consistente para o cliente '{client}', com a menor variação de QoE de {qoe_variance}."

        User: "Qual é a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente rj entre as 08 e 09h do dia 07/06/2024?"
        Input Data: {datahora}, {server_change_strategy}
        AI: Entre 08:00 e 09:00 do dia 07/06/2024, a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente '{client}' é a seguinte:
            - datahora_1: server_change_strategy_1."
            - datahora_2: server_change_strategy_2."
            - datahora_3: server_change_strategy_3."
            ...

        User: "Se a latência aumentar 20%, como isso afeta a QoE do cliente rj e servidor pi entre as 08 e 09h do dia 07/06/2024?"
        Input Data: {datahora}, {QoE}, {new_QoE}
        AI: Se a latência aumentar 20% entre 08:00 e 09:00 do dia 07/06/2024 para o cliente '{client}' e servidor '{server}', a qualidade de experiência (QoE) mudaria da seguinte maneira:
            - datahora: De QoE_1 para new_QoE_1."
            - datahora: De QoE_2 para new_QoE_2."
            - datahora: De QoE_3 para new_QoE_3."
            ...

        User: "Qual o endereço de IP do cliente rj na rede?"
        Input Data: {info} = "Pergunta não compreendida."
        AI: Não possuo em meu banco de dados o endereço de IP do cliente rj na rede. Por favor, ente outra pergunta relacionada à rede ou aos dados disponíveis."

        User: "Qual é a previsão do tempo para amanhã?"
        Input Data: {info} = "Pergunta não compreendida."
        AI: Desculpe, mas não tenho informações sobre a previsão do tempo. Por favor, ente outra pergunta relacionada à rede ou aos dados disponíveis."

        **Final Instructions**:
        - Always adapt the response based on the question and the specific data provided.
        - Ensure clarity and coherence in the final response.
    """

    # Cria o template com as variáveis extraídas
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_4), ("human", "{processed_data}")])
    response_llm = prompt | llm.with_structured_output(NaturalLanguageResponse)
    response = response_llm.invoke(data)

    return response.response


def responder_pergunta(pergunta):
    """Função principal que executa todo o encadeamento para responder a pergunta do usuário."""
    
    # 1. Compreensão da Pergunta
    print("Step 1: Compreendendo a pergunta...")
    passos_logicos = step_1_comprehend_question(pergunta)
    
    # 2. Geração de Flags
    print("Step 2: Gerando flags...")
    flags = step_2_generate_flags(passos_logicos)
    
    # 4. Processamento dos Dados com base nas flags
    print("Step 3: Processando os dados com base nas flags...")
    dados_processados, _ = step_3_process_with_flags(pergunta, flags)
    
    # 5. Geração de Resposta em Linguagem Natural
    print("Step 4: Gerando a resposta em linguagem natural...")
    resposta_final = step_4_generate_response(dados_processados)

    # Imprime a resposta gerada
    print(f"Resposta gerada: {resposta_final}")
    print("\n")

    
    return resposta_final


