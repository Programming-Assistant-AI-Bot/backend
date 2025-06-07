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
    
    def remove_documents_by_metadata(self, session_id, metadata_filter):
        """Remove documents from session based on metadata filter."""
        if not self.session_exists(session_id):
            return False
        
        try:
            db = self.get_session_db(session_id)
            
            # Get all documents with their IDs
            docs_and_scores = db.similarity_search_with_score("", k=10000)  # Get all docs
            
            # Find documents that match the filter
            docs_to_remove = []
            ids_to_remove = []
            
            for i, (doc, score) in enumerate(docs_and_scores):
                # Check if document matches the filter criteria
                should_remove = True
                for key, value in metadata_filter.items():
                    if doc.metadata.get(key) != value:
                        should_remove = False
                        break
                
                if should_remove:
                    docs_to_remove.append(doc)
                    ids_to_remove.append(str(i))  # FAISS uses string IDs
            
            if ids_to_remove:
                # Remove documents by recreating the index without them
                remaining_docs = []
                for i, (doc, score) in enumerate(docs_and_scores):
                    if str(i) not in ids_to_remove:
                        remaining_docs.append(doc)
                
                # Recreate the FAISS index with remaining documents
                if remaining_docs:
                    new_db = FAISS.from_documents(remaining_docs, self.embeddings)
                else:
                    # If no documents remain, create with dummy document
                    dummy_doc = Document(page_content="[DUMMY INIT]", metadata={"init": True})
                    new_db = FAISS.from_documents([dummy_doc], self.embeddings)
                
                # Save the updated index
                new_db.save_local(self.get_session_path(session_id))
                
            return len(ids_to_remove)
            
        except Exception as e:
            print(f"Error removing documents: {e}")
            return False
    
    def remove_documents_by_file_id(self, session_id, file_id):
        """Remove all documents associated with a specific file ID."""
        return self.remove_documents_by_metadata(session_id, {"file_id": file_id})