from langchain_ollama import OllamaLLM
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
import os
from dotenv import load_dotenv
import asyncio
from pymongo import MongoClient
from services.chatHistory.mongoClassHistory import LimitedMongoDBChatMessageHistory



load_dotenv()
DB_URL = os.getenv("DB_URL")

mongo_client = MongoClient(DB_URL)
try:
    # Create indexes for better query performance
    mongo_client.Chatbot.Messages.create_index([("sessionId", 1)])
    mongo_client.Chatbot.Messages.create_index([("sessionId", 1), ("_id", -1)])
    print("MongoDB indexes created successfully")
except Exception as e:
    print(f"Warning: Failed to create MongoDB indexes: {e}")


system_prompt = (
    "Given a chat history and the latest user question "
    "Based on chathistory answer the current question "
    "You are the code assistant named Archelon AI. Use the most recent chat history to answer questions when necessary. Always provide complete responses and do not add 'Human:' at the end of your responses. "
    "when generating code block following this format "
    "```[respective programming language name]\n"
    "[Your code here]\n"
    "```"
)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),  # Ensure this matches `history_messages_key`
    ("human", "{input}"),
])


# Initialize the LLM
# llm = OllamaLLM(model="codellama:latest")
llm = OllamaLLM(model="qwen2.5-coder:0.5b")
parser = StrOutputParser()
llm_chain = qa_prompt| llm | parser



def get_session_history(session_id: str) -> BaseChatMessageHistory:
    return LimitedMongoDBChatMessageHistory(
        connection_string=DB_URL,
        database_name="Chatbot",
        collection_name="Messages",
        session_id=session_id,
        limit=20  # Limit to last 20 messages
    )

conversational_chain = RunnableWithMessageHistory(
    llm_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

def get_callback_handler():
    return AsyncIteratorCallbackHandler()


# async def testLLM():
#     question = input("Enter the prompt: ")
#     sessionId = "123"
#     callback_handler = get_callback_handler()
#     result = await conversational_chain.ainvoke(
#         {"input":question},  # Use the actual question rather than "Test message"
#         config={"configurable": {"session_id": sessionId},"callbacks": [callback_handler]}
#     )
#     print(result)
#     await asyncio.sleep(1)

# asyncio.run(testLLM())

