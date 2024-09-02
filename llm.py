from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import sqlite3
import os
from env import OPENAI_API_KEY # key armazenada em um arquivo que está no .gitignore para manter o sigilo
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


# Inicialização do modelo de linguagem
llm = ChatOpenAI(model="gpt-4o-mini")

class DatabaseQuery(BaseModel):
    """Structure for database queries."""
    table: str = Field(description="The name of the table to be read from the database")
    query: str = Field(description="The SQL query to fetch data from the database")

class NaturalLanguageResponse(BaseModel):
    """Structure for natural language responses."""
    response: str = Field(description="The natural language response based on the question and the result")

def process_query(pergunta):
    # Exemplo de sistema para orientar a LLM
    system = """You are an expert in network performance data analysis. You understand the format of the SQLite database: trabalho_raw.db with tables bitrate_train and rtt_train.

    Here are some examples of queries and their structured responses:

    example_user: Qual foi o cliente com maior bitrate?
    example_assistant: {{"table": "bitrate_train", "query": "SELECT client, MAX(bitrate) as Max_Bitrate FROM bitrate_train GROUP BY client ORDER BY Max_Bitrate DESC LIMIT 1"}}

    example_user: Qual foi o servidor com menor rtt?
    example_assistant: {{"table": "rtt_train", "query": "SELECT server, MIN(rtt) as Min_RTT FROM rtt_train GROUP BY server ORDER BY Min_RTT ASC LIMIT 1"}}

    example_user: Qual foi a média do bitrate por cliente?
    example_assistant: {{"table": "bitrate_train", "query": "SELECT client, AVG(bitrate) as Avg_Bitrate FROM bitrate_train GROUP BY client"}}

    example_user: Qual foi a média do rtt por servidor?
    example_assistant: {{"table": "rtt_train", "query": "SELECT server, AVG(rtt) as Avg_RTT FROM rtt_train GROUP BY server"}}"""

    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])

    few_shot_structured_llm = prompt | llm.with_structured_output(DatabaseQuery)
    table_and_query = few_shot_structured_llm.invoke(pergunta)
    
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect('trabalho_raw.db')
    
    # Executar a query SQL usando a conexão SQLite
    query_result = pd.read_sql_query(table_and_query.query, conn)
    
    # Fechar a conexão
    conn.close()
    
    return query_result, table_and_query

def generate_nl_response(pergunta, query_result):
    result_str = query_result.to_string(index=False)
    
    nl_system = """You are an expert in network performance data analysis. You provide concise and clear natural language responses based on the user's query and the result of the data analysis.

    Here are some examples:

    example_user: Qual foi o cliente com maior bitrate?
    example_assistant: O cliente com maior bitrate foi [client] com um bitrate de [Max_Bitrate].

    example_user: Qual foi o servidor com menor rtt?
    example_assistant: O servidor com menor rtt foi [server] com um rtt de [Min_RTT] ms.

    example_user: Qual foi a média do bitrate por cliente?
    example_assistant: A média do bitrate por cliente foi de [Avg_Bitrate] para o cliente [client].

    example_user: Qual foi a média do rtt por servidor?
    example_assistant: A média do rtt por servidor foi de [Avg_RTT] ms para o servidor [server]."""

    nl_prompt = ChatPromptTemplate.from_messages([("system", nl_system), ("human", "{input}")])
    nl_structured_llm = nl_prompt | llm.with_structured_output(NaturalLanguageResponse)
    
    response = nl_structured_llm.invoke({"input": f"Pergunta: {pergunta}\nResultado: {result_str}"})
    return response.response


if __name__ == "__main__":
    pergunta = "Qual foi o cliente com maior bitrate?"
    query_result, table_and_query = process_query(pergunta)
    print(table_and_query)
    print(query_result)
    response = generate_nl_response(pergunta, query_result)
    print(response)

