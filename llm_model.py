from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
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
    You are an AI that understands questions related to databases, specifically focusing on network measurements stored in SQL tables. Your job is to understand the user's question, considering the specific context of the data, and determine the necessary logical steps to answer it.

    Important Context:
    - The 'bitrate' is stored in the 'bitrate_train' table and is measured in bursts. A burst is defined by measurements with very close timestamps (less than 5 seconds apart). When calculating an average for a burst, it refers to the average bitrate within this short time interval.
    - Latency is stored in the 'rtt' column of the 'rtt_train' table and is measured continuously but irregularly over time, without bursts.
    - Timestamps are stored in Unix time in both tables and can be matched between tables for analysis.
    - The 'bitrate_train' table has the following columns: client, server, timestamp, bitrate.
    - The 'rtt_train' table has the following columns: client, server, timestamp, rtt.

    Given these details, analyze the user's question, determine what needs to be calculated, and outline the logical steps needed to construct the appropriate SQL query or handle the question context.

    **Handling Questions**:

    1. **Questions Not Related to the Database**:
       - If the question is unrelated to network scope (e.g., asking for weather information or general knowledge), recognize that it is unrelated to the database.
       - If the question is related to network measurements or the network context (e.g., IP addresses, client-server information) but does not fit into the provided examples (e.g., it asks for specific types of analysis or metrics not described), recognize the question is unrelated to the database but cannot be answered.       

    **Examples**:

        User: "Qual cliente tem a pior qualidade de recepção de vídeo ao longo do tempo?"
        Logical Steps:
        1. Calculate QoE for each client using bitrate from 'bitrate_train' and latency (RTT) from 'rtt_train'.
        2. Ensure that the QoE calculation is only performed when the latency measurement coincides with a burst of bitrate measurements.
        3. Normalize both the bitrate and latency.
        4. Calculate QoE for each client over time.
        5. Identify the client with the lowest average QoE.

        User: "Qual servidor fornece a QoE mais consistente?"
        Logical Steps:
        1. Calculate QoE for each server based on clients connected to it, using the 'bitrate_train' and 'rtt_train' tables.
        2. Ensure that the QoE calculation is only performed when the latency measurement coincides with a burst of bitrate measurements.
        3. Calculate the variance of QoE for each server.
        4. Identify the server with the lowest variance in QoE.

        User: "Qual é a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente X?"
        AI: The user is asking for an optimal strategy to switch servers over time to improve QoE for a specific client. The logical steps are:
            1. Identify all servers that the client is connected to from the 'bitrate_train' and 'rtt_train' tables.
            2. Calculate the QoE for each server over time.
            3. Determine the best server at each timestamp to maximize QoE for the client.
            4. Recommend the best server switching strategy based on QoE.

        User: "Se a latência aumentar 20%, como isso afeta a QoE do cliente Y?"
        AI: The user is asking to simulate the effect of increased latency on QoE. The logical steps are:
            1. Select the client and retrieve their current latency values from 'rtt_train'.
            2. Increase the latency values by 20%.
            3. Recalculate QoE using the modified latency values.
            4. Compare the new QoE values to the original and explain the impact of the latency change.

        User: "Qual o bitrate médio dentro de cada rajada para o cliente X e o servidor Y no período entre 07/06/2024 e 10/06/2024?"
        AI: The user is asking for the average bitrate within bursts for a specific client and server over a given time period. The logical steps are:
            1. Filter the 'bitrate_train' table for measurements related to client X and server Y within the time period.
            2. Identify bursts by grouping measurements that occur within 5 seconds of each other.
            3. Calculate the average bitrate for each identified burst.

        User: "Qual a latência nas medições que coincidem com a janela de tempo das rajadas de medição de bitrate para o cliente X e o servidor Y no período entre 07/06/2024 e 10/06/2024?"
        AI: The user is asking to find the latency (from the 'rtt_train' table) that matches the time intervals of bursts identified in the 'bitrate_train' table for a specific client and server. The logical steps are:
            1. Filter the 'bitrate_train' table for measurements related to client X and server Y within the time period.
            2. Identify bursts by grouping measurements that occur within 5 seconds of each other.
            3. Find the corresponding latency measurements in the 'rtt_train' table that fall within the same time intervals as the bursts.
            4. Return these latency measurements.
    """

    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_1), ("human", "{input}")])
    logical_steps_llm = prompt | llm.with_structured_output(LogicalSteps)
    logical_steps = logical_steps_llm.invoke(question)
    return logical_steps

class FlagOutput(BaseModel):
    """Estrutura para as flags geradas com base nos passos lógicos."""
    qoe_required: bool = Field(default=False, description="Flag para indicar se a QoE precisa ser calculada")
    latency_increase: bool = Field(default=False, description="Flag para indicar se a latência será aumentada")
    server_variance: bool = Field(default=False, description="Flag para indicar se a variância do servidor será calculada")
    bitrate_average: bool = Field(default=False, description="Flag para indicar se a média do bitrate por rajada deve ser calculada")
    latency_for_bursts: bool = Field(default=False, description="Flag para indicar se a latência deve ser calculada nas rajadas")
    unrelated_to_db: bool = Field(default=False, description="Flag para indicar que a pergunta não está relacionada ao banco de dados")
    client_specific: str = Field(default=False, description="Nome do cliente específico, se aplicável, ou False")
    server_specific: str = Field(default=False, description="Nome do servidor específico, se aplicável, ou False")
    datahora_inicio: str = Field(default=False, description="Data de início do intervalo de tempo ou False")
    datahora_final: str = Field(default=False, description="Data final do intervalo de tempo ou False")



def step_2_generate_flags(logical_steps):
    """Step 2: Geração de Flags com base nos passos lógicos"""

    system_prompt_2 = """
    You are an AI that generates flags based on logical steps describing the actions needed to answer a user's question related to network measurement data stored in SQL tables.

    Given the logical steps, generate flags to indicate the required calculations or to handle specific situations:
    
    - Set 'qoe_required' to True if the question requires calculating the Quality of Experience (QoE).
    - Set 'latency_increase' to True if the question involves simulating an increase in latency.
    - Set 'server_variance' to True if the question asks for the variance in QoE across servers.
    - Set 'bitrate_average' to True if the question involves calculating the average bitrate within bursts.
    - Set 'latency_for_bursts' to True if the question asks for latency values that match burst intervals from the 'bitrate_train' table.
    - Set 'unrelated_to_db' to True if the question is not directly related to the available network measurement data in the database (e.g., IP addresses, network topology, or general knowledge like weather or geography).
    - Set 'client_specific' and 'server_specific' to the names of the client and server if the question specifies them; otherwise, keep them as "False".
    - Set 'datahora_inicio' and 'datahora_final' to the start and end timestamps if the question specifies a time range, formatted as 'YYYY-MM-DD HH:MM:SS'; otherwise, keep them as "False".

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

    User: "Qual servidor fornece a QoE mais consistente?"
    Logical Steps:
    1. Calculate QoE for each server based on clients connected to it, using the 'bitrate_train' and 'rtt_train' tables.
    2. Normalize both the bitrate and latency.
    3. Ensure that QoE is only calculated when the latency coincides with a burst of bitrate.
    4. Calculate the variance of QoE for each server.
    5. Identify the server with the lowest variance in QoE.

    User: "Qual é a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente ba?"
    Logical Steps:
    1. Identify all servers that the client is connected to from the 'bitrate_train' and 'rtt_train' tables.
    2. Calculate the QoE for each server over time.
    3. Determine the best server at each timestamp to maximize QoE for the client.
    4. Recommend the best server switching strategy based on QoE.
    Flags: qoe_required = True, client_specific = 'ba'

    User: "Se a latência aumentar 20%, como isso afeta a QoE do cliente rj?"
    Logical Steps:
    1. Select the client and retrieve their current latency values from 'rtt_train'.
    2. Increase the latency values by 20%.
    3. Recalculate QoE using the modified latency values.
    4. Compare the new QoE values to the original and explain the impact of the latency change.
    Flags: latency_increase = True, qoe_required = True, client_specific = 'rj'

    User: "Qual o bitrate médio dentro de cada rajada para o cliente ba e o servidor pi no período entre 2024-06-07 00:00:00 e 2024-06-10 23:59:59?"
    Logical Steps:
    1. Filter the 'bitrate_train' table for measurements related to client ba and server pi within the time period.
    2. Identify bursts by grouping measurements that occur within 5 seconds of each other.
    3. Calculate the average bitrate for each identified burst.
    Flags: bitrate_average = True, client_specific = 'ba', server_specific = 'pi', datahora_inicio = '2024-06-07 00:00:00', datahora_final = '2024-06-10 23:59:59'

    User: "Qual a latência nas medições que coincidem com a janela de tempo das rajadas de medição de bitrate para o cliente rj e o servidor df no período entre 2024-06-07 00:00:00 e 2024-06-10 23:59:59?"
    Logical Steps:
    1. Filter the 'bitrate_train' table for measurements related to client rj and server df within the time period.
    2. Identify bursts by grouping measurements that occur within 5 seconds of each other.
    3. Find the corresponding latency measurements in the 'rtt_train' table that fall within the same time intervals as the bursts.
    4. Return these latency measurements.
    Flags: latency_for_bursts = True, client_specific = 'rj', server_specific = 'df', datahora_inicio = '2024-06-07 00:00:00', datahora_final = '2024-06-10 23:59:59'

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
    flag_llm = prompt | llm.with_structured_output(FlagOutput)
    flags = flag_llm.invoke(logical_steps)
    return flags

def step_3_process_with_flags(flags):
    """Step 3: Processa os dados com base nas flags geradas no step_2."""
    
    processed_data = {}

    # Verifica se a pergunta é considerada não relacionada ao banco de dados
    if flags.unrelated_to_db:
        processed_data['info'] = "A pergunta não está relacionada ao banco de dados disponível."
        return processed_data
    
    # Extrai os DataFrames do banco de dados (essa função deve lidar com a extração dos dados)
    bitrate_df, rtt_df = aux_get_dataframes_from_db()

    # Aplica os filtros de cliente e/ou servidor, se necessário
    if flags.client_specific != "False":
        bitrate_df = bitrate_df[bitrate_df['client'] == flags.client_specific]
        rtt_df = rtt_df[rtt_df['client'] == flags.client_specific]
    if flags.server_specific != "False":
        bitrate_df = bitrate_df[bitrate_df['server'] == flags.server_specific]
        rtt_df = rtt_df[rtt_df['server'] == flags.server_specific]

    # Aplica o filtro de tempo com base no timestamp, se necessário
    if flags.datahora_inicio != "False" and flags.datahora_final != "False":
        # Converte datahora para timestamp utilizando a função auxiliar
        timestamp_inicio = aux_convert_datahora_to_timestamp(flags.datahora_inicio)
        timestamp_final = aux_convert_datahora_to_timestamp(flags.datahora_final)
        
        # Filtra os DataFrames usando a coluna timestamp
        bitrate_df = bitrate_df[(bitrate_df['timestamp'] >= timestamp_inicio) & (bitrate_df['timestamp'] <= timestamp_final)]
        rtt_df = rtt_df[(rtt_df['timestamp'] >= timestamp_inicio) & (rtt_df['timestamp'] <= timestamp_final)]

    # Flag para calcular a QoE apenas quando a latência coincidir com uma rajada de bitrate
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
    
    # Flag para simular aumento de latência
    if flags.latency_increase:
        merged_df = pd.merge(bitrate_df, rtt_df, on=['client', 'server', 'timestamp'])
        merged_df['Simulated QoE'] = merged_df.apply(lambda row: aux_simular_qoe_com_aumento_latencia(
            row['bitrate'], row['rtt'], 20, min_bitrate=100, max_bitrate=10000, min_rtt=10, max_rtt=500), axis=1)
        simulated_qoe_by_client = merged_df.groupby('client')['Simulated QoE'].mean().to_dict()
        processed_data['Simulated QoE'] = simulated_qoe_by_client
    
    # Flag para calcular a variância da QoE por servidor
    if flags.server_variance:
        merged_df = pd.merge(bitrate_df, rtt_df, on=['client', 'server', 'timestamp'])
        merged_df['QoE'] = merged_df.apply(lambda row: aux_calcular_qoe(row['bitrate'], row['rtt'], 
                                                                       min_bitrate=100, max_bitrate=10000, 
                                                                       min_rtt=10, max_rtt=500), axis=1)
        variance_by_server = merged_df.groupby('server')['QoE'].var().to_dict()
        processed_data['QoE Variance'] = variance_by_server
    
    # Flag para calcular o bitrate médio por rajada
    if flags.bitrate_average:
        bursts = aux_calculate_bitrate_bursts(bitrate_df)
        processed_data['Bitrate Average'] = bursts
    
    # Flag para calcular a latência para as rajadas de bitrate
    if flags.latency_for_bursts:
        latency_for_bursts = aux_find_latency_for_bursts(bitrate_df, rtt_df)
        processed_data['Latency for Bursts'] = latency_for_bursts
    
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


