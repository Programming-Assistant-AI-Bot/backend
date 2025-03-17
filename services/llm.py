from langchain_ollama import OllamaLLM
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain_core.output_parsers import StrOutputParser

callback_handler = AsyncIteratorCallbackHandler()

parser = StrOutputParser()

llm = OllamaLLM(
        model="codellama:latest",
        callbacks=[callback_handler]
      )
            
# Initialize the chain
parser = StrOutputParser()
llm_chain = llm | parser


