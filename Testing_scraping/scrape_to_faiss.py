import requests
from bs4 import BeautifulSoup
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# --- STEP 1: Scrape Website ---
def scrape_website(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer"]):
            element.decompose()
        
        text = soup.get_text(separator=" ", strip=True)
        return text
    except Exception as e:
        print(f"Scraping failed: {e}")
        return None

# --- STEP 2: Clean & Chunk Text ---
def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

# --- STEP 3: Generate Embeddings ---
model = SentenceTransformer('BAAI/bge-small-en')

def get_embeddings(texts):
    return model.encode(texts)

# --- STEP 4: Store in FAISS Index ---
def create_faiss_index(embeddings):
    dimension = embeddings.shape[1]  # Get embedding dimension (e.g., 384 for 'bge-small-en')
    index = faiss.IndexFlatL2(dimension)  # L2 distance metric
    index.add(embeddings)  # Add embeddings to index
    return index

# --- STEP 5: Save/Load FAISS Index ---
def save_faiss_index(index, file_path):
    faiss.write_index(index, file_path)

def load_faiss_index(file_path):
    return faiss.read_index(file_path)

# --- RUN THE PIPELINE ---
if __name__ == "__main__":
    # Example: Scrape a website
    url = "https://example.com/docs"  # Replace with your target URL
    scraped_text = scrape_website(url)
    
    if scraped_text:
        chunks = chunk_text(scraped_text)
        embeddings = get_embeddings(chunks)
        
        # Convert to numpy array (FAISS requires float32)
        embeddings = np.array(embeddings).astype('float32')
        
        # Create and save FAISS index
        index = create_faiss_index(embeddings)
        save_faiss_index(index, "faiss_index.bin")
        print(f"Saved FAISS index with {len(chunks)} chunks.")
        
        # (Optional) Query the index
        query = "How to fix API errors?"
        query_embedding = get_embeddings([query]).astype('float32')
        k = 3  # Number of results to retrieve
        distances, indices = index.search(query_embedding, k)
        print(f"Top {k} results for query: {query}")
        for i, idx in enumerate(indices[0]):
            print(f"{i+1}. {chunks[idx]} (Distance: {distances[0][i]:.2f})")
    else:
        print("Scraping failed. Check the URL or try another site.")