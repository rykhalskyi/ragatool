import asyncio
from abc import ABC, abstractmethod
from threading import Event
from typing import List
from fastapi import UploadFile
from sentence_transformers import SentenceTransformer
import chromadb

class ImportBase(ABC):
    name: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int

    @abstractmethod
    def create_chunks(self, text: str) -> List[str]:
        pass

    @abstractmethod
    async def import_data(self, collection_name: str, file: UploadFile, cancel_event:Event) -> None:
        pass

class FileImport(ImportBase):
    name = "FILE"
    embedding_model = "all-MiniLM-L6-v2"
    chunk_size = 300
    chunk_overlap = 50

    def create_chunks(self, text: str) -> List[str]:
        return [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

    async def import_data(self, collection_name: str, file: UploadFile, cancel_event: Event) -> None:
        text_content = ""
        byte_content =await file.read()
            
        text_content = byte_content.decode("utf-8")

        chunks = self.create_chunks(text_content)

        model = SentenceTransformer(self.embedding_model, trust_remote_code=True)
        embeddings = model.encode(chunks)

        client = chromadb.PersistentClient(path="./chroma_data")
        collection = client.get_or_create_collection(name=collection_name)

        collection.upsert(
            documents=chunks,
            embeddings=embeddings.tolist(),
            metadatas=[{"source": file.filename, "chunk": i} for i in range(len(chunks))],
            ids=[f"{file.filename}_chunk_{i}" for i in range(len(chunks))]
        )
