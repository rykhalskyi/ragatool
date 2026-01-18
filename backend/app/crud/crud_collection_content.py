import chromadb
from fastembed import TextEmbedding

embedder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

def get_collection_chunks(collection_id: str, page: int, page_size: int):
    """
    Retrieves all items from a ChromaDB collection and returns a paginated dictionary.
    """
    try:
        client = chromadb.PersistentClient(path="./chroma_data")
        collection = client.get_collection(name=collection_id)
        
        all_items = collection.get()
        
        total_chunks = len(all_items["ids"])
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        paginated_ids = all_items["ids"][start_index:end_index]
        paginated_documents = all_items["documents"][start_index:end_index]
        
        result_chunks = []
        for i in range(len(paginated_ids)):
            result_chunks.append({"id": paginated_ids[i], "document": paginated_documents[i]})
        
        return {
            "chunks": result_chunks,
            "total_chunks": total_chunks,
            "page": page,
            "page_size": page_size,
        }
    except ValueError as e:
        raise ValueError(f"Collection '{collection_id}' not found. {str(e)}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")

def query_collection(collection_id: str, query_text: str, n_results: int = 10):
    """
    Queries a collection with a given text.
    """
    try:
        client = chromadb.PersistentClient(path="./chroma_data")
        collection = client.get_collection(name=collection_id)
        
        query_embedding = list(embedder.embed([query_text]))[0].tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )
        return {"status": "success", "results": results}
    except ValueError as e:
        raise ValueError(f"Collection '{collection_id}' not found. {str(e)}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")
