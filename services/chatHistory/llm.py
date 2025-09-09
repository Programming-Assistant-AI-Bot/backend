from operator import itemgetter
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import trim_messages
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory

from vectordb.persistentFaiss import PersistentSessionStorage
from services.chatHistory.mongoClassHistory import LimitedMongoDBChatMessageHistory

# —— Load environment variables ——
load_dotenv()
DB_URL = os.getenv("DB_URL")

# —— MongoDB chat‐history helper ——
mongo_client = MongoClient(DB_URL)
# Ensure indexes
mongo_client.Chatbot.Messages.create_index([("sessionId", 1)])
mongo_client.Chatbot.Messages.create_index([("sessionId", 1), ("_id", -1)])

def get_session_history(session_id: str, user_id: str) -> BaseChatMessageHistory:
    return LimitedMongoDBChatMessageHistory(
        connection_string=DB_URL,
        database_name="Chatbot",
        collection_name="Messages",
        session_id=session_id,
        user_id=user_id,
        limit=20
    )

# —— Per-session FAISS storage helper ——
storage = PersistentSessionStorage(base_directory="./session_storage")

# —— LLM & Parser ——
# Enable streaming on the OllamaLLM
llm = OllamaLLM(
    model="perlbot3:latest",
    streaming=True,
    model_kwargs={"num_ctx": 32768}

)
parser = StrOutputParser()

# —— Prompt Templates ——
SYSTEM_TEXT = (
    "You are Archelon AI, a highly specialized assistant focused exclusively on Perl programming. "
    "Your role is to provide accurate, detailed, and effective solutions to Perl-related coding problems. "
    "When responding to user queries, take into account the full chat history and any specific context provided. "

    "Response Guidelines:\n"
    "- Always default to Perl for code generation unless the user explicitly specifies another language.\n"
    "- Provide complete, executable solutions with well-structured Perl code.\n"
    "- Format all code blocks using proper markdown syntax: perl\\n...code...\\n\n"
    "- Include clear and helpful comments within your code when useful for understanding.\n"
    "- If referencing earlier messages, be specific about which part is relevant and why.\n"
    "- For non-coding questions, provide concise, accurate answers\n"
    

    "Your primary goal is to assist developers by delivering correct, readable, and best-practice Perl code.\n"
    "Be concise but thorough, and always prioritize code clarity and functionality.\n\n"
    "{context}"
)
SYSTEM_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_TEXT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])

CONTEXTUALIZE_TEXT = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)
CONTEXTUALIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", CONTEXTUALIZE_TEXT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])

# Trimmer to keep token count within limits
TRIMMER = trim_messages(
    max_tokens=3000,
    strategy="last",
    token_counter=llm,
    include_system=True,
    start_on="human"
)

# —— Build & wrap the RAG chain inside a function ——  
def make_conversational_chain(session_id: str, user_id: str):
    # 1. Load or create the per-session FAISS vector store for this user
    faiss_db = storage.create_or_load(user_id, session_id)
    retriever = faiss_db.as_retriever(search_type="mmr", kwargs={"k": 3})

    # 2. Wrap retriever to reformulate follow-ups
    history_retriever = create_history_aware_retriever(
        llm, retriever, CONTEXTUALIZE_PROMPT
    )

    # 3. Build the QA chain (with trimming + parser)
    qa_chain = (
        RunnablePassthrough
          .assign(chat_history=itemgetter("chat_history")|TRIMMER)
        | SYSTEM_PROMPT
        | llm
        | parser
    )

    # 4. Combine into a RAG chain
    rag_chain = create_retrieval_chain(history_retriever, qa_chain)

    # 5. Wrap with persistent chat history including user context
    get_session_history_for_user = lambda session_id: get_session_history(session_id, user_id)
    
    conversational = RunnableWithMessageHistory(
        rag_chain,
        get_session_history_for_user,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )

    return conversational
