from langchain_ollama import OllamaLLM
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain_core.output_parsers import StrOutputParser

# Remove the global callback handler
# callback_handler = AsyncIteratorCallbackHandler()

parser = StrOutputParser()

# Create LLM without attaching the callback handler
llm = OllamaLLM(
        model="codellama:latest"
      )
            
# Initialize the chain
parser = StrOutputParser()
llm_chain = llm | parser

# Create a function to get a new callback handler for each request
def get_callback_handler():
    return AsyncIteratorCallbackHandler()


