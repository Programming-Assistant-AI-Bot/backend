from langchain_ollama import OllamaLLM
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage,HumanMessage,BaseMessage
from typing import List
import json
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
import os
from dotenv import load_dotenv
import asyncio
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from pymongo import MongoClient
from datetime import datetime,timezone


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

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the code assistant named Archelon AI. Use the most recent chat history to answer questions when necessary."),
    MessagesPlaceholder(variable_name="chat_history"),  # Ensure this matches `history_messages_key`
    ("human", "{input}"),
])


# Initialize the LLM
llm = OllamaLLM(model="codellama:latest")
parser = StrOutputParser()
llm_chain = qa_prompt| llm | parser

class LimitedMongoDBChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, connection_string, database_name, collection_name, session_id, limit=20):
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.session_id = session_id
        self.limit = limit
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve messages from MongoDB based on your specific data structure"""
        # Get the most recent entries for this session
        cursor = self.collection.find(
            {"sessionId": self.session_id}
        ).sort("timestamp",1).limit(self.limit)
        
        # Process the documents
        message_list = []
        for doc in cursor:
            try:
                # Parse the History field which contains the JSON string
                history_data = doc
                
                # Create the appropriate message type
                if history_data["role"] == "user":
                    message = HumanMessage(content=history_data["content"])
                elif history_data["role"] == "assistant":
                    message = AIMessage(content=history_data["content"])
                else:
                    continue  # Skip unknown message types
                
                message_list.append(message)
            except (json.JSONDecodeError, KeyError) as e:
                # Handle errors gracefully
                print(f"Error parsing message: {e}")
                continue
        
        # Reverse to get chronological order
        message_list.reverse()
        return message_list
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the history"""
        # Convert the message to a JSON-serializable format
        if isinstance(message, HumanMessage):
            message_type = "user"
        elif isinstance(message, AIMessage):
            message_type = "assistant"
        else:
            message_type = "other"
        
        # Create the History field
        history_data = {
            "sessionId":self.session_id,
            "role": message_type,
            "content": message.content,
            "timestamp":datetime.now(timezone.utc)
        }
        
        # Insert into MongoDB
        self.collection.insert_one(history_data)
    
    def clear(self) -> None:
        """Clear the history"""
        self.collection.delete_many({"sessionId": self.session_id})

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

# asyncio.run(testLLM())

