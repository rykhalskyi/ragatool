import asyncio
from abc import ABC, abstractmethod
from threading import Event
from typing import List
from fastapi import UploadFile
from sentence_transformers import SentenceTransformer
import chromadb
import time
from app.internal.message_hub import message_hub # New import

class ImportBase(ABC):
    name: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int

    @abstractmethod
    def create_chunks(self, text: str) -> List[str]:
        pass

    @abstractmethod
    async def import_data(self, collection_id: str, collection_name: str, file: UploadFile, cancel_event:Event) -> None: # Modified signature
        pass

class FileImport(ImportBase):
    name = "FILE"
    embedding_model = "all-MiniLM-L6-v2"
    chunk_size = 300
    chunk_overlap = 50

    def create_chunks(self, text: str) -> List[str]:
        return [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

    async def import_data(self, collection_id: str, collection_name: str, file: UploadFile, cancel_event: Event) -> None: # Modified signature
        try:
            message_hub.send_message(collection_id, collection_name, "LOCK", f"Starting import of {file.filename}")
            
            collection_name = collection_name.lower().replace(' ','_')
            text_content = ""
            byte_content =await file.read()
                
            text_content = byte_content.decode("utf-8")

            chunks = self.create_chunks(text_content)
            message_hub.send_message(collection_id, collection_name, "LOG", f"Created {len(chunks)} chunks")

            model = SentenceTransformer(self.embedding_model, trust_remote_code=True)
            embeddings = model.encode(chunks)
            message_hub.send_message(collection_id, collection_name, "LOG", "Embeddings created")

            client = chromadb.PersistentClient(path="./chroma_data")
            collection = client.get_or_create_collection(name=collection_name)

            ts = int(time.time())
            # ---- batching logic ----
            max_batch_size = 5000  # safe limit below Chroma's 5461 cap

            batch_num = 1
            for start in range(0, len(chunks), max_batch_size):
                end = start + max_batch_size

                batch_chunks = chunks[start:end]
                batch_embeddings = embeddings[start:end].tolist()

                batch_ids = [
                    f"{file.filename}_{ts}_{i}"
                    for i in range(start, min(end, len(chunks)))
                ]

                collection.upsert(
                    documents=batch_chunks,
                    embeddings=batch_embeddings,
                    metadatas=[{"source": file.filename, "chunk": i, "ts":ts} for i in range(start, min(end, len(chunks)))],
                    ids=batch_ids
                )

                message_hub.send_message(collection_id, collection_name, "LOG", f"Import of batch {batch_num} completed successfully")
                batch_num += 1
                
            message_hub.send_message(collection_id, collection_name, "UNLOCK", f"Import of {file.filename} completed successfully")
        except Exception as e:
            message_hub.send_message(collection_id, collection_name, "UNLOCK", f"Import of {file.filename} failed: {e}")
            print("import_data", e)
