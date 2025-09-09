from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def get_split_chunks_from_pdf(pdf_file_path: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> list:

    # Load the PDF document.
    loader = PyPDFLoader(pdf_file_path)
    docs = loader.load()
    
    # Initialize the text splitter with specified chunking parameters.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_documents(docs)
    
    return chunks