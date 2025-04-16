from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
import os
import shutil

class PersistentSessionStorage:
    def __init__(self, base_directory="./session_storage", model_name="all-MiniLM-L6-v2"):
        """Initialize storage with base directory and HuggingFace embeddings."""
        self.base_directory = base_directory
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        os.makedirs(base_directory, exist_ok=True)
    
    def get_session_path(self, session_id):
        """Return the directory path for the given session ID."""
        # Convert session_id to string if it's not already for consistent folder naming.
        return os.path.join(self.base_directory, str(session_id))
    
    def session_exists(self, session_id):
        """Return whether the session exists."""
        session_path = self.get_session_path(session_id)
        index_file = os.path.join(session_path, "index.faiss")
        return os.path.exists(session_path) and os.path.exists(index_file)
    
    def create_session(self, session_id, initial_documents=None):
        """Create a new session with an optional list of initial documents."""
        session_path = self.get_session_path(session_id)
        if os.path.exists(session_path):
            return session_id  # session already exists
        
        os.makedirs(session_path)
        if initial_documents:
            db = FAISS.from_documents(initial_documents, self.embeddings)
        else:
            # FAISS needs at least one document; using a dummy initialization document.
            dummy_doc = Document(page_content="[DUMMY INIT]", metadata={"init": True})
            db = FAISS.from_documents([dummy_doc], self.embeddings)
        db.save_local(session_path)
        return session_id
    
    def get_session_db(self, session_id):
        """Load and return the FAISS index for the given session."""
        session_path = self.get_session_path(session_id)
        if not os.path.exists(session_path):
            raise ValueError(f"Session {session_id} does not exist")
        return FAISS.load_local(session_path, self.embeddings,allow_dangerous_deserialization=True)
        
    def add_documents_to_session(self, session_id, documents):
        """Add documents to an existing session and update the FAISS index."""
        if not self.session_exists(session_id):
            # Create a new session with the provided documents.
            self.create_session(session_id, documents)
            return
        # For an existing session:
        db = self.get_session_db(session_id)
        db.add_documents(documents)
        db.save_local(self.get_session_path(session_id))


    
    def delete_session(self, session_id):
        """Delete the session directory."""
        session_path = self.get_session_path(session_id)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
            return True
        return False

    def create_or_load(self, session_id, initial_documents=None):
        """
        Load the FAISS database for an existing session,
        or create a new session (with optional initial documents) if it doesn't exist.
        """
        if self.session_exists(session_id):
            db = self.get_session_db(session_id)
        else:
            self.create_session(session_id, initial_documents)
            db = self.get_session_db(session_id)
        return db