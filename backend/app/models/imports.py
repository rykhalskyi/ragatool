from abc import ABC, abstractmethod
from threading import Event
from typing import List
from fastembed import TextEmbedding
import chromadb
import time
import numpy as np
from pathlib import Path

from app.internal.message_hub import MessageHub
from app.models.messages import MessageType
from app.schemas.imports import Import
from app.internal.temp_file_helper import TempFileHelper

# Import LangChain loaders
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import PyPDFLoader
#from langchain_community.document_loaders import PyMuPDFLoader

class ImportBase(ABC):
    name: str
    settings: Import

    @abstractmethod
    async def import_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, import_params: Import, message_hub:MessageHub, cancel_event:Event) -> None: # Modified signature
        pass

    @abstractmethod
    async def prepare_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, message_hub: MessageHub) -> str:
        pass    

    def create_chunks(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]


        
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
                chunk_overlap=80,
                no_chunks=False
            )
        )
    
    async def prepare_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, message_hub: MessageHub) -> str:
        """
        Prepares file content for chunking.
        Handles different file types (TXT, MD, DOCX, PDF).
        """
        file_extension = Path(file_name).suffix.lower()
        extracted_text = ""
        temp_file_path = None

        try:
            if file_extension in [".docx", ".pdf"]:
                temp_file_path = TempFileHelper.save_temp(file_content_bytes, file_name)

                try:
                    loader = None
                    if file_extension == ".docx":
                        loader = Docx2txtLoader(temp_file_path)
                        message_hub.send_message(collection_id, MessageType.INFO, f"Parsing DOCX file '{file_name}' with Docx2txtLoader.")
                    elif file_extension == ".pdf":
                        
                        loader = PyPDFLoader(temp_file_path)
                        message_hub.send_message(collection_id, MessageType.INFO, f"Parsing PDF file '{file_name}' with PDFPlumberLoader.")
                    
                    if loader != None:
                        docs = loader.load() 
                        extracted_text = "\n".join([doc.page_content.replace('\n','') for doc in docs])

                except Exception as e:
                    message_hub.send_message(collection_id, MessageType.INFO, f"Error parsing {file_extension.upper()} file '{file_name}': {e}")
                    raise RuntimeError(f"Failed to parse {file_extension.upper()} file '{file_name}': {e}") from e
            elif file_extension in [".txt", ".md"]:
                extracted_text = file_content_bytes.decode("utf-8")
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        finally:
            if temp_file_path:
                TempFileHelper.remove_temp(temp_file_path)
        
        return extracted_text

    async def import_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, import_params: Import, message_hub:MessageHub, cancel_event: Event) -> None: # Modified signature
        file_extension = Path(file_name).suffix.lower()
        try:
            message_hub.send_message(collection_id,  MessageType.LOCK, f"Starting import of {file_name}")
                          
            text_content = await self.prepare_data(collection_id, file_name, file_content_bytes, message_hub)
            
            if cancel_event.is_set():
                 message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} was cancelled")
                 message_hub.send_message(collection_id, MessageType.LOG, f"CANCELLED Import {file_extension.upper()} from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
                 return

            chunks = []
            if not import_params.settings.no_chunks:
                chunks = self.create_chunks(text_content, import_params.settings.chunk_size, import_params.settings.chunk_overlap)
            else:
                chunks = [text_content]

            message_hub.send_message(collection_id, MessageType.INFO, f"Created {len(chunks)} chunks. Embedding....")

            #new embedder
            embedder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
            embeddings = np.array(list(embedder.embed(chunks)))

            if cancel_event.is_set():
                 message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} was cancelled")
                 message_hub.send_message(collection_id, MessageType.LOG, f"CANCELLED Import {file_extension.upper()} from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
                 return

            message_hub.send_message(collection_id, MessageType.INFO, "Embeddings created. Saving to Database....")

            client = chromadb.PersistentClient(path="./chroma_data")
            collection = client.get_or_create_collection(name=collection_id, metadata={"hnsw:space": "cosine"} )

            ts = int(time.time())
            # ---- batching logic ----
            max_batch_size = 5000  # safe limit below Chroma's 5461 cap

            batch_num = 1
            for start in range(0, len(chunks), max_batch_size):
                if cancel_event.is_set():
                    message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} was cancelled")
                    message_hub.send_message(collection_id, MessageType.LOG, f"CANCELLED Import {file_extension.upper()} from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
                    return

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
            message_hub.send_message(collection_id, MessageType.LOG, f"SUCCESSFUL imported {file_extension.upper()} from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
        except Exception as e:
            print("FAIL import_data", e)
            message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} failed: {e}")
            message_hub.send_message(collection_id, MessageType.LOG, f"FAILED import {file_extension.upper()} from {file_name}. Chunk size {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}. Exception {e}")
            

            
        
