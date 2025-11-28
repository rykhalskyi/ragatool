from abc import ABC, abstractmethod
from threading import Event
from typing import List
from sentence_transformers import SentenceTransformer
import chromadb
import time
from app.internal.message_hub import MessageHub
from app.models.messages import MessageType
from app.schemas.imports import Import

class ImportBase(ABC):
    name: str
    settings: Import

    @abstractmethod
    def create_chunks(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        pass

    @abstractmethod
    async def import_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, import_params: Import, message_hub:MessageHub, cancel_event:Event) -> None: # Modified signature
        pass

from app.schemas.imports import Import, FileImportSettings

class FileImport(ImportBase):
    name = "FILE"

    @staticmethod
    def getDefault() -> Import:
        return Import(
            name="FILE",
            model="all-MiniLM-L6-v2",
            settings=FileImportSettings(
                chunk_size=800,
                chunk_overlap=10,
                no_chunks=False
            )
        )

    def create_chunks(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]

    async def import_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, import_params: Import, message_hub:MessageHub, cancel_event: Event) -> None: # Modified signature
        try:
            message_hub.send_message(collection_id,  MessageType.LOCK, f"Starting import of {file_name}")
                       
    
            text_content = file_content_bytes.decode("utf-8")

            chunks = []
            if not import_params.settings.no_chunks:
                chunks = self.create_chunks(text_content, import_params.settings.chunk_size, import_params.settings.chunk_overlap)
            else:
                chunks = [text_content]

            message_hub.send_message(collection_id, MessageType.INFO, f"Created {len(chunks)} chunks. Embedding....")

            model = SentenceTransformer(import_params.model, trust_remote_code=True)
            embeddings = model.encode(chunks)
            message_hub.send_message(collection_id, MessageType.INFO, "Embeddings created. Saving to Database....")

            client = chromadb.PersistentClient(path="./chroma_data")
            collection = client.get_or_create_collection(name=collection_id)

            ts = int(time.time())
            # ---- batching logic ----
            max_batch_size = 5000  # safe limit below Chroma's 5461 cap

            batch_num = 1
            for start in range(0, len(chunks), max_batch_size):
                end = start + max_batch_size

                batch_chunks = chunks[start:end]
                batch_embeddings = embeddings[start:end].tolist()

                batch_ids = [
                    f"{file_name}_{ts}_{i}"
                    for i in range(start, min(end, len(chunks)))
                ]

                collection.upsert(
                    documents=batch_chunks,
                    embeddings=batch_embeddings,
                    metadatas=[{"source": file_name, "chunk": i, "ts":ts} for i in range(start, min(end, len(chunks)))],
                    ids=batch_ids
                )

                message_hub.send_message(collection_id, MessageType.INFO, f"Import of batch {batch_num} completed successfully")
                batch_num += 1
                
            message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} completed successfully")
            message_hub.send_message(collection_id, MessageType.LOG, f"SUCCESSFUL imported from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
        except Exception as e:
            print("FAIL import_data", e)
            message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} failed: {e}")
            message_hub.send_message(collection_id, MessageType.LOG, f"FAILED import from {file_name}. Chunk size {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}. Exception {e}")
            

            
        
