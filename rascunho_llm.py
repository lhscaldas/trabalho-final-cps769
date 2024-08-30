from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from typing import Union, Optional
import os
from env import OPENAI_API_KEY # key armazenada em um arquivo que está no .gitignore para manter o sigilo
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

class Joke(BaseModel):
    """Joke to tell user."""
    setup: str = Field(description="The setup of the joke")
    punchline: str = Field(description="The punchline to the joke")
    rating: Optional[int] = Field(description="How funny the joke is, from 1 to 10")

class ConversationalResponse(BaseModel):
    """Respond in a conversational manner. Be kind and helpful."""

    response: str = Field(description="A conversational response to the user's query")

class Response(BaseModel):
    output: Union[Joke, ConversationalResponse]

llm = ChatOpenAI(model="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY,
)

structured_llm = llm.with_structured_output(Joke)

system = """You are a hilarious comedian. Your specialty is knock-knock jokes. \
Return a joke which has the setup (the response to "Who's there?") and the final punchline (the response to "<setup> who?").

Here are some examples of jokes:

example_user: Tell me a joke about planes
example_assistant: {{"setup": "Why don't planes ever get tired?", "punchline": "Because they have rest wings!", "rating": 2}}

example_user: Tell me another joke about planes
example_assistant: {{"setup": "Cargo", "punchline": "Cargo 'vroom vroom', but planes go 'zoom zoom'!", "rating": 10}}

example_user: Now about caterpillars
example_assistant: {{"setup": "Caterpillar", "punchline": "Caterpillar really slow, but watch me turn into a butterfly and steal the show!", "rating": 5}}"""

prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])

few_shot_structured_llm = prompt | structured_llm

few_shot_structured_llm.invoke("what's something funny about woodpeckers")







