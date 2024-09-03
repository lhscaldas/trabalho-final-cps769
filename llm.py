from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import sqlite3
import os
from env import OPENAI_API_KEY

# Configuração da chave de API
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Inicialização do modelo de linguagem
llm = ChatOpenAI(model="gpt-4o-mini")

class LogicalSteps(BaseModel):
    """Estrutura para os passos lógicos necessários."""
    steps: str = Field(description="Passos lógicos necessários para responder à pergunta")

class StructuredThoughts(BaseModel):
    """Estrutura para o processo de raciocínio estruturado."""
    structured_steps: str = Field(description="Processo de raciocínio estruturado necessário para construir a query")

class DatabaseQuery(BaseModel):
    """Estrutura para a query SQL final."""
    table: str = Field(description="O nome da tabela a ser lida no banco de dados")
    query: str = Field(description="A query SQL para buscar os dados no banco de dados")

class NaturalLanguageResponse(BaseModel):
    """Structure for natural language responses."""
    response: str = Field(description="The natural language response based on the question and the result")

def model_1_understand_question(question):
    """Modelo 1: Compreensão da Pergunta"""
    system_prompt_1 = """
        You are an AI that understands questions related to databases, specifically focusing on network measurements stored in SQL tables. Your job is to understand the user's question, considering the specific context of the data, and determine the necessary logical steps to answer it.

        Important Context:
        - The 'bitrate' is stored in the 'bitrate_train' table and is measured in bursts. A burst is defined by measurements with very close timestamps (less than 5 seconds apart). When calculating an average for a burst, it refers to the average bitrate within this short time interval.
        - Latency is stored in the 'rtt' column of the 'rtt_train' table and is measured continuously but irregularly over time, without bursts.

        Given these details, analyze the user's question, determine what needs to be calculated, and outline the logical steps needed to construct the appropriate SQL query.

        Examples:
        - User: What is the average bitrate rate in each burst?
        AI: The user is asking for the average bitrate within each burst. The logical steps are:
            1. Identify bursts in the 'bitrate_train' table by grouping measurements that occur within 5 seconds of each other.
            2. Calculate the average bitrate for each identified burst.
        
        - User: What is the latency of measurements that coincide with a burst?
        AI: The user is asking to find the latency (from the 'rtt_train' table) that matches the time intervals of bursts identified in the 'bitrate_train' table. The logical steps are:
            1. Identify bursts in the 'bitrate_train' table.
            2. For each burst, find the corresponding latency measurements in the 'rtt_train' table based on overlapping timestamps.
            3. Return these latency measurements.
    """
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_1), ("human", "{input}")])
    logical_steps_llm = prompt | llm.with_structured_output(LogicalSteps)
    logical_steps = logical_steps_llm.invoke(question)
    return logical_steps

def model_2_structure_thoughts(logical_steps):
    """Modelo 2: Estruturação do Pensamento"""
    system_prompt_2 = """
        You are an AI that structures thought processes for constructing SQL queries. Based on the logical steps provided, outline a structured reasoning process that will lead to the creation of the SQL query.

        Important Context:
        - When identifying bursts in the 'bitrate_train' table, group measurements that occur within 5 seconds of each other. The average bitrate for a burst should be calculated for each of these groups.
        - When matching latency measurements to bursts, ensure that the timestamps in the 'rtt_train' table overlap with the timestamps of the bursts identified in the 'bitrate_train' table.

        Use the provided logical steps to create a detailed and structured plan for the SQL query.

        Example Logical Steps:
        1. Identify bursts in the 'bitrate_train' table by grouping measurements within 5 seconds.
        2. Calculate the average bitrate for each burst.
        3. Retrieve the latency measurements that overlap with these bursts from the 'rtt_train' table.

        Example Structured Thoughts:
        1. Select the relevant table ('bitrate_train').
        2. Define a window of 5 seconds to group measurements into bursts.
        3. Calculate the average bitrate for each burst using GROUP BY and HAVING clauses.
        4. For latency matching, perform a JOIN or a subquery with the 'rtt_train' table where timestamps overlap with the identified bursts.
        5. Construct the final SQL query using these steps.
    """
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_2), ("human", "{input}")])
    structured_thoughts_llm = prompt | llm.with_structured_output(StructuredThoughts)
    structured_thoughts = structured_thoughts_llm.invoke(logical_steps.steps)
    return structured_thoughts

def model_3_generate_query(structured_thoughts):
    """Modelo 3: Geração da Query SQL"""
    system_prompt_3 = """
        You are an AI that generates SQL queries based on a structured thought process. Use the structured reasoning provided to create a SQL query.

        Important Context:
        - The `timestamp` column is stored as Unix time in seconds.
        - The `datahora` column is stored in the format 'YYYY-MM-DD HH:MM:SS'.
        - We need to generate queries that work with these formats, converting between Unix time and the human-readable `datahora` format when necessary.
        - A burst in the 'bitrate_train' table consists of measurements with `timestamp` values that are within 5 seconds of each other. We should group these timestamps to calculate the average bitrate for each burst.
        - When matching latency measurements to bursts, we should identify overlapping timestamps between the 'rtt_train' and 'bitrate_train' tables.

        Examples for average bitrate in each burst:
        - Example Structured Thoughts:
        1. Select the 'bitrate_train' table.
        2. Use a self-join or subquery to group measurements into bursts by identifying `timestamp` values that are within 5 seconds of each other.
        3. Calculate the average bitrate for each burst, as well as the start and end timestamps.
        4. For latency matching, perform a JOIN with the 'rtt_train' table where `timestamp` values overlap with the identified bursts.
        5. Convert Unix `timestamp` to 'YYYY-MM-DD HH:MM:SS' format for human-readable results.
        6. Return the necessary fields.
        - Example SQL Query:
        {{
            "table": "bitrate_train",
            "query": "
            SELECT 
                AVG(b1.bitrate) as Avg_Bitrate, 
                MIN(DATETIME(b1.timestamp, 'unixepoch')) as Burst_Start, 
                MAX(DATETIME(b1.timestamp, 'unixepoch')) as Burst_End
            FROM bitrate_train b1
            WHERE EXISTS (
            SELECT 1 FROM bitrate_train b2
            WHERE b1.client = b2.client 
                AND b1.server = b2.server 
                AND ABS(b1.timestamp - b2.timestamp) <= 5
            )
            GROUP BY (b1.timestamp / 5);
            "
        }}
        """

    #     Examples to identify bursts and calculate the average latency for each burst:
    #     - Example Structured Thoughts:
    #     1. Select the 'bitrate_train' table and filter the data between 08:00 and 09:00 on 07/06/2024, for the client 'rj' and server 'pi'.
    #     2. Use a self-join to create groups (bursts) where the difference between consecutive timestamps is 5 seconds or less.
    #     3. For each burst, determine the `timestamp` of the start (minimum) and end (maximum) of the burst.
    #     4. Use these `timestamp` intervals to filter the `rtt_train` table and calculate the average `rtt` for each burst interval.
    #     5. Return the `datahora` interval and the average `rtt`.
    #     - Example SQL Query:
    #     {{
    #         "table": "bitrate_train",
    #         "query": "
    #         WITH bursts AS (
    #         SELECT 
    #             MIN(b1.timestamp) AS Burst_Start,
    #             MAX(b1.timestamp) AS Burst_End,
    #             MIN(b1.datahora) AS Burst_Start_Time,
    #             MAX(b1.datahora) AS Burst_End_Time
    #         FROM bitrate_train b1
    #         JOIN bitrate_train b2 ON b1.client = b2.client 
    #             AND b1.server = b2.server 
    #             AND b1.timestamp BETWEEN b2.timestamp AND b2.timestamp + 5
    #         WHERE b1.client = 'rj'
    #         AND b1.server = 'pi'
    #         AND b1.timestamp BETWEEN strftime('%s', '2024-06-07 08:00:00') AND strftime('%s', '2024-06-07 09:00:00')
    #         GROUP BY b1.timestamp
    #         )
    #         SELECT 
    #             bursts.Burst_Start_Time,
    #             bursts.Burst_End_Time,
    #             AVG(rtt.rtt) as Avg_RTT
    #         FROM rtt_train rtt
    #         JOIN bursts ON rtt.timestamp BETWEEN bursts.Burst_Start AND bursts.Burst_End
    #         GROUP BY bursts.Burst_Start_Time, bursts.Burst_End_Time;
    #         "
    #     }}
    # """
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_3), ("human", "{input}")])
    database_query_llm = prompt | llm.with_structured_output(DatabaseQuery)
    final_query = database_query_llm.invoke(structured_thoughts.structured_steps)
    return final_query

def execute_sql_query(query):
    """Executa a query SQL e retorna o resultado."""
    try:
        conn = sqlite3.connect('trabalho_raw.db')
        query_result = pd.read_sql_query(query, conn)
        conn.close()
        return query_result
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Erro ao executar a query: {query}") from e

def model_4_nl_response(question, query_result):
    """Gera uma resposta em linguagem natural baseada na pergunta e no resultado da query."""
    result_str = query_result.to_string(index=False)
    
    system_prompt_4 = """You are an expert in network performance data analysis. You provide concise and clear natural language responses based on the user's query and the result of the data analysis.

    Here are some examples:

    example_user: Qual foi o cliente com maior bitrate?
    example_assistant: O cliente com maior bitrate foi [client] com um bitrate de [Max_Bitrate].

    example_user: Média da taxa de bitrate em cada rajada para cada par cliente-servidor?
    example_assistant: A média da taxa de bitrate em cada rajada para o par cliente-servidor [client]-[server] no timestamp [timestamp] foi de [Avg_Bitrate].

    example_user: Medida da latência que coincide com uma rajada de bitrate?
    example_assistant: A latência mínima que coincide com uma rajada de bitrate foi de [Latency] ms para o par cliente-servidor [client]-[server] no timestamp [timestamp]."""

    nl_prompt = ChatPromptTemplate.from_messages([("system", system_prompt_4), ("human", "{input}")])
    nl_structured_llm = nl_prompt | llm.with_structured_output(NaturalLanguageResponse)
    
    response = nl_structured_llm.invoke({"input": f"Pergunta: {question}\nResultado: {result_str}"})
    return response.response

if __name__ == "__main__":
    question = "Qual a média da taxa de bitrate para o cliente rj e servidor pi para cada rajada entre 8 e 9h do dia 07/06/2024?"
    # question = "Qual a latência média das medições que coincidem com cada rajada de bitrate para o cliente rj e servidor pi entre 8 e 9h do dia 07/06/2024?"
    logical_steps = model_1_understand_question(question)
    print(logical_steps)
    structured_thoughts = model_2_structure_thoughts(logical_steps)
    print(structured_thoughts)
    final_query = model_3_generate_query(structured_thoughts)
    print(final_query)
    query_result = execute_sql_query(final_query.query)
    print(query_result)
    response = model_4_nl_response(question, query_result)
    print(response)