from langchain_core.chat_history import BaseChatMessageHistory
from pymongo import MongoClient
from langchain_core.messages import BaseMessage,AIMessage,HumanMessage
from typing import List
import json
from datetime import datetime,timezone
from models.chatMessages import Message

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
        history_data = Message(
            sessionId=self.session_id,
            role = message_type,
            content= message.content,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Insert into MongoDB
        self.collection.insert_one(history_data.model_dump())
    
    def clear(self) -> None:
        """Clear the history"""
        self.collection.delete_many({"sessionId": self.session_id})