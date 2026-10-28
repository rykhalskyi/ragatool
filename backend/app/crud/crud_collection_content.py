from app.internal import vector_store
from app.internal.retrieval import retrieve


def get_collection_chunks(collection_id: str, page: int, page_size: int):
    """
    Retrieves all items from a ChromaDB collection and returns a paginated dictionary.
    """
    try:
        collection = vector_store.get_collection(collection_id)

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
    Queries a collection using the shared retrieval pipeline (vector + rerank).
    """
    try:
        return retrieve(collection_id, query_text, n_results=n_results)
    except ValueError as e:
        raise ValueError(f"Collection '{collection_id}' not found. {str(e)}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")
