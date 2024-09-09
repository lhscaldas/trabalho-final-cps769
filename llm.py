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
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
    )

class LogicalSteps(BaseModel):
    """Estrutura para os passos lógicos necessários."""
    steps: str = Field(description="Passos lógicos necessários para responder à pergunta")
