import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

router = APIRouter()

# Project-relative path to the test-text file. This resolves relative to the repository
# layout so the code works across environments (no hard-coded absolute Windows path).
# The file is located at: <project-root>/test-text/greek-mythology-1.md
# We move up 2 parents from this file (app/routers) to reach the repo 'backend' folder.
BASE_DIR = Path(__file__).resolve().parents[2]
TEXT_FILE_PATH = BASE_DIR / "test-text" / "greek-mythology-1.md"
MODEL = 'all-MiniLM-L6-v2'
#MODEL = 'nomic-ai/nomic-embed-text-v1'

# Directory where Chroma will persist its database files (repo-local)
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"


def get_chroma_client():
    """Create a chromadb client configured to persist to CHROMA_PERSIST_DIR.

    This helper ensures the persist directory exists and returns a client using
    DuckDB+Parquet (stable, file-backed) storage.
    """
    # ensure the directory exists
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    settings = Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=str(CHROMA_PERSIST_DIR),
    )

    # Support both calling conventions for different chromadb versions
    try:
        client = chromadb.Client(settings)
    except TypeError:
        client = chromadb.Client(settings=settings)
    return client

def embed_and_store_text() -> dict:
    # Create a dummy text file for demonstration if it doesn't exist
    try:
        if not TEXT_FILE_PATH.exists():
            TEXT_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            TEXT_FILE_PATH.write_text(
                "This is a sample document for the proof of concept. It contains some text that will be embedded and stored."
            )
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dummy text file: {e}")

    try:
        text_content = TEXT_FILE_PATH.read_text()
        # Split the text into chunks (you can adjust the chunk size)
        chunks = [text_content[i:i+500] for i in range(0, len(text_content), 500)]
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to read text file: {e}")

    # Load SentenceTransformer model
    try:
        model = SentenceTransformer(MODEL,trust_remote_code=True)
    except Exception as e:
        print("Failed to load SentenceTransformer model", e)
        raise HTTPException(status_code=500, detail=f"Failed to load SentenceTransformer model: {e}")

    # Generate embeddings for each chunk
    try:
        embeddings = model.encode(chunks)
    except Exception as e:
        print("Faled to embed", e)
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {e}")

    # Initialize ChromaDB client and collection
    try:
        client = chromadb.PersistentClient(path="./chroma_data")
        collection = client.get_or_create_collection(name="poc")
    except Exception as e:
        print("Chroma client error", e)
        raise HTTPException(status_code=500, detail=f"Failed to initialize ChromaDB or get collection: {e}")

    # Store embeddings for each chunk
    try:
        collection.upsert(
            documents=chunks,
            embeddings=embeddings.tolist(),
            metadatas=[{"source": str(TEXT_FILE_PATH), "chunk": i} for i in range(len(chunks))],
            ids=[f"chunk_{i}" for i in range(len(chunks))]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store embeddings in ChromaDB: {e}")

    return {"status": "Text embedded and stored successfully in chromadb."}

@router.get("/poc/")
def run_proof_of_concept():
    return embed_and_store_text()

@router.get("/check/")
def check_chromadb(query: str) -> dict:
    try:
        model = SentenceTransformer(MODEL,trust_remote_code=True)
    except Exception as e:
        print('transformer',e)
        raise HTTPException(status_code=500, detail=f"Failed to load SentenceTransformer model: {e}")
    
    try:
        query_embedding = model.encode([query]).tolist()
    except Exception as e:
        print('query',e)
        raise HTTPException(status_code=500, detail=f"Failed to encode query: {e}")

    try:
        client = chromadb.PersistentClient(path="./chroma_data")
        collection = client.get_or_create_collection(name="drakula")
    except Exception as e:
        print('connect to db',e)
        raise HTTPException(status_code=500, detail=f"Failed to initialize ChromaDB or get collection: {e}")

    try:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=3  # Return top 3 most relevant chunks
        )
    except Exception as e:
        print('run query',e)
        raise HTTPException(status_code=500, detail=f"Failed to query ChromaDB: {e}")
    
    if results and results['documents']:
        return {
            "results": results['documents'][0],  # Most relevant chunk
            "additional_results": results['documents'][1:],  # Other relevant chunks
            "distances": results['distances']  # Similarity scores
        }
    return {"results": "No matching documents found."}



