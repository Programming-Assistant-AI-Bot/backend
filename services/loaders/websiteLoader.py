from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def get_split_chunks_from_url(
    url: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    ssl_verify: bool = True,
    headers: dict = None
) -> list:

    # Set default headers if none are provided.
    if headers is None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            )
        }
    
    # Load the URL content.
    loader = UnstructuredURLLoader(
        urls=[url],
        ssl_verify=ssl_verify,
        headers=headers
    )
    docs = loader.load()
    print(f"Loaded {len(docs)} documents from the URL.")
    
    # Initialize the text splitter.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    # Split the documents into chunks.
    chunks = text_splitter.split_documents(docs)
    print(f"Generated {len(chunks)} chunks from the documents.")
    
    return chunks