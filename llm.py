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

class DatabaseQuery(BaseModel):
    """Structure for database queries."""
    table: str = Field(description="The name of the table to be read from the database")
    query: str = Field(description="The SQL query to fetch data from the database")

def generate_query(question):
    """Gera a query SQL a partir da pergunta."""
    system_prompt = """
        You are an AI assistant that helps with SQL queries. Based on the user's question, determine the necessary table and construct the appropriate SQL query. 

        Here are some examples of queries and their structured responses:

        example_user: Qual foi o cliente com maior bitrate?
        example_assistant: {{"table": "bitrate_train", "query": "SELECT client, MAX(bitrate) as Max_Bitrate FROM bitrate_train GROUP BY client ORDER BY Max_Bitrate DESC LIMIT 1"}}

        example_user: Média da taxa de bitrate em cada rajada para cada par cliente-servidor?
        example_assistant: {{"table": "bitrate_train", "query": "SELECT client, server, datahora, AVG(bitrate) as Avg_Bitrate FROM bitrate_train GROUP BY client, server, datahora"}}

        example_user: Média da taxa de bitrate para o cliente rj e servidor pi no dia 07/06/2024?
        example_assistant: {{"table": "bitrate_train", "query": "SELECT client, server, datahora, AVG(bitrate) as Avg_Bitrate FROM bitrate_train WHERE client = 'rj' AND server = 'pi' AND datahora BETWEEN '2024-06-07 00:00:00' AND '2024-06-07 23:59:59' GROUP BY client, server, datahora"}}

        example_user: Média do bitrate para o servidor pb entre os dias 01/05/2024 e 10/05/2024?
        example_assistant: {{"table": "bitrate_train", "query": "SELECT AVG(bitrate) as Avg_Bitrate FROM bitrate_train WHERE server = 'pb' AND datahora BETWEEN '2024-05-01 00:00:00' AND '2024-05-10 23:59:59'"}}

        example_user: Qual foi o menor RTT registrado para os clientes do estado rj que usaram o servidor pi no mês de julho de 2024?
        example_assistant: {{"table": "rtt_train", "query": "SELECT MIN(rtt) as Min_RTT FROM rtt_train WHERE client LIKE 'rj%' AND server = 'pi' AND datahora BETWEEN '2024-07-01 00:00:00' AND '2024-07-31 23:59:59'"}}

        example_user: Quantos registros de bitrate existem na tabela bitrate_train?
        example_assistant: {{"table": "bitrate_train", "query": "SELECT COUNT(*) as Record_Count FROM bitrate_train"}}
    """

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
    few_shot_database_query_llm = prompt | llm.with_structured_output(DatabaseQuery)
    table_and_query = few_shot_database_query_llm.invoke(question)
    return table_and_query

def execute_sql_query(query):
    """Executa a query SQL e retorna o resultado."""
    try:
        conn = sqlite3.connect('trabalho_raw.db')
        query_result = pd.read_sql_query(query, conn)
        conn.close()
        return query_result
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Erro ao executar a query: {query}") from e
    
class NaturalLanguageResponse(BaseModel):
    """Structure for natural language responses."""
    response: str = Field(description="The natural language response based on the question and the result")

def generate_nl_response(question, query_result):
    """Gera uma resposta em linguagem natural baseada na pergunta e no resultado da query."""
    result_str = query_result.to_string(index=False)
    
    nl_system_prompt = """You are an expert in network performance data analysis. You provide concise and clear natural language responses based on the user's query and the result of the data analysis.

    Here are some examples:

    example_user: Qual foi o cliente com maior bitrate?
    example_assistant: O cliente com maior bitrate foi [client] com um bitrate de [Max_Bitrate].

    example_user: Média da taxa de bitrate em cada rajada para cada par cliente-servidor?
    example_assistant: A média da taxa de bitrate em cada rajada para o par cliente-servidor [client]-[server] no timestamp [timestamp] foi de [Avg_Bitrate].

    example_user: Medida da latência que coincide com uma rajada de bitrate?
    example_assistant: A latência mínima que coincide com uma rajada de bitrate foi de [Latency] ms para o par cliente-servidor [client]-[server] no timestamp [timestamp]."""

    nl_prompt = ChatPromptTemplate.from_messages([("system", nl_system_prompt), ("human", "{input}")])
    nl_structured_llm = nl_prompt | llm.with_structured_output(NaturalLanguageResponse)
    
    response = nl_structured_llm.invoke({"input": f"Pergunta: {question}\nResultado: {result_str}"})
    return response.response

if __name__ == "__main__":
    question = "Média da taxa de bitrate para o cliente rj e servidor pi entre 8 e 9h do dia 07/06/2024?"
    table_and_query = generate_query(question)
    print(table_and_query)
    query_result = execute_sql_query(table_and_query.query)
    print(query_result)
    response = generate_nl_response(question, query_result)
    print(response)