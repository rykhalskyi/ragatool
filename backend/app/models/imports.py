from abc import ABC, abstractmethod
import os
import re
from threading import Event
from typing import List
from app.internal.embedding_manager import (
    DEFAULT_EMBEDDING_MODEL,
    embed_documents,
    resolve_embedding_model,
)
from app.internal import vector_store
import time
import numpy as np
from pathlib import Path

from app.internal.chunker import Chunker, ChunkType
from app.crud.crud_files import create_file, delete_file, get_files_for_collection
from app.internal.message_hub import MessageHub
from app.models.import_context import ImportContext
from app.models.messages import MessageType
from app.schemas.imports import Import
from app.internal.temp_file_helper import TempFileHelper

# Import LangChain loaders
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import PyPDFLoader

from app.schemas.setting import SettingsName
#from langchain_community.document_loaders import PyMuPDFLoader

class ImportBase(ABC):
    name: str
    settings: Import

    
    @abstractmethod
    async def import_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, context: ImportContext, cancel_event:Event) -> None: # Modified signature
        pass

    @abstractmethod
    async def prepare_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, message_hub: MessageHub) -> str:
        pass    
    
    def check_cancelled(self, collection_id: str, file_name: str, message_hub: MessageHub, cancel_event: Event) -> bool:
        if cancel_event.is_set():
            message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} was cancelled")
            message_hub.send_message(collection_id, MessageType.LOG, f"CANCELLED Import from {file_name} ")
            return True
        return False    
        
from app.schemas.imports import Import, FileImportSettings

class FileImport(ImportBase):
    name = "FILE"

    @staticmethod
    def getDefault() -> Import:
        return Import(
            name="FILE",
            model=DEFAULT_EMBEDDING_MODEL,
            settings=FileImportSettings(
                chunk_size=800,
                chunk_overlap=80,
                no_chunks=False,
                chunk_type=ChunkType.RECURSIVE_CHARACTER
            )
        )

    def _get_or_create_collection(self, collection_id: str, import_params: Import):
        """
        Returns the Chroma collection together with the embedding model it was
        created with. Existing collections keep their model so new chunks are
        never embedded with a different model than the stored vectors.
        """
        client = vector_store.get_client()
        try:
            collection = client.get_collection(name=collection_id)
            return collection, vector_store.get_collection_embedding_model(collection)
        except Exception:
            embedding_model = resolve_embedding_model(import_params.model)
            collection = vector_store.get_or_create_collection(
                collection_id, embedding_model=embedding_model, client=client
            )
            return collection, embedding_model

    def _process_chunks_and_store(self, collection_id: str, file_name: str, file_extension: str, chunks: List[dict], import_params: Import, message_hub: MessageHub, cancel_event: Event) -> None:
        """Embed chunks and store them in ChromaDB with batching and cancellation support."""
        message_hub.send_message(collection_id, MessageType.INFO, f"Created {len(chunks)} chunks. Embedding....")

        collection, embedding_model = self._get_or_create_collection(collection_id, import_params)
        embeddings = np.array(list(embed_documents([chunk["text"] for chunk in chunks], embedding_model)))

        if self.check_cancelled(collection_id, file_name, message_hub, cancel_event):
            return

        message_hub.send_message(collection_id, MessageType.INFO, "Embeddings created. Saving to Database....")

        ts = int(time.time())
        # ---- batching logic ----
        max_batch_size = 5000  # safe limit below Chroma's 5461 cap

        batch_num = 1
        for start in range(0, len(chunks), max_batch_size):

            if self.check_cancelled(collection_id, file_name, message_hub, cancel_event):
                return

            end = start + max_batch_size

            batch_records = chunks[start:end]
            batch_embeddings = embeddings[start:end].tolist()

            batch_ids = [
                f"{file_name}_{ts}_{i}"
                for i in range(start, min(end, len(chunks)))
            ]

            metadatas = [
                {
                    "source": file_name,
                    "chunk": i,
                    "ts": ts,
                    "char_start": record["start"],
                    "char_end": record["start"] + len(record["text"]),
                }
                for i, record in zip(range(start, min(end, len(chunks))), batch_records)
            ]

            collection.upsert(
                documents=[record["text"] for record in batch_records],
                embeddings=batch_embeddings,
                metadatas=metadatas,
                ids=batch_ids
            )

            message_hub.send_message(collection_id, MessageType.INFO, f"Import of batch {batch_num} completed successfully")
            batch_num += 1
            
        message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} completed successfully")
        message_hub.send_message(collection_id, MessageType.LOG, f"SUCCESSFUL imported {file_extension.upper()} from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
    
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
                        # Preserve paragraph and line structure: the recursive
                        # splitter relies on newlines to keep chunks coherent.
                        extracted_text = "\n\n".join(
                            doc.page_content for doc in docs if doc.page_content
                        )

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

        return self._normalize_text(extracted_text)

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Collapses runs of spaces but keeps paragraph breaks intact."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    async def import_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, context: ImportContext, cancel_event: Event) -> None: # Modified signature
        file_extension = Path(file_name).suffix.lower()
        message_hub = context.messageHub
        import_params = context.parameters
        try:
            
            message_hub.send_message(collection_id,  MessageType.LOCK, f"Starting import of {file_name}")
                          
            text_content = await self.prepare_data(collection_id, file_name, file_content_bytes, message_hub)
            
            if self.check_cancelled(collection_id, file_name, message_hub, cancel_event):
                return

            chunks = []
            if not import_params.settings.no_chunks:
                chunks = Chunker().create_chunks_with_offsets(text_content, import_params.settings.chunk_type , import_params.settings.chunk_size, import_params.settings.chunk_overlap)
            else:
                chunks = [{"text": text_content, "start": 0}]

            # delegate embedding + DB storage to helper
            self._process_chunks_and_store(collection_id, file_name, file_extension, chunks, import_params, message_hub, cancel_event)
        except Exception as e:
            print("FAIL import_data", e)
            message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} failed: {e}")
            message_hub.send_message(collection_id, MessageType.LOG, f"FAILED import {file_extension.upper()} from {file_name}. Chunk size {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}. Exception {e}")
            
    
    async def step_1(self, collection_id: str, file_name: str, file_content_bytes: bytes, context: ImportContext, cancel_event:Event) -> None: # Modified signature
        if not context.settings.check(SettingsName.TWO_STEP_IMPORT, 'True'):
            context.messageHub.send_message(collection_id, MessageType.INFO, "Set 2 Step mode to use this function")
            return
        
        context.messageHub.send_message(collection_id, MessageType.LOCK, f"Step 1 of import of {file_name} started")
        text_content = await self.prepare_data(collection_id, file_name, file_content_bytes, context.messageHub)

        tmp_file = TempFileHelper.save_temp_str(text_content, file_name)
        create_file(context.db, collection_id, tmp_file, file_name)
        context.messageHub.send_message(collection_id, MessageType.UNLOCK, f"Step 1 of import of {file_name} completed successfully")

    
    async def step_2(self, collection_id: str, context: ImportContext, files_ids: List[str], cancel_event:Event) -> None: # Modified signature
        if not context.settings.check(SettingsName.TWO_STEP_IMPORT, 'True'):
             context.messageHub.send_message(collection_id, MessageType.INFO, "Set 2 Step mode to use this function")
             return
        
        files = get_files_for_collection(context.db, collection_id)
        if len(files) == 0:
            return
        
        for file in files:
            try:
                if file.id not in files_ids:
                    continue
                if os.path.exists(file.path):
                    with open(file.path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        if self.check_cancelled(collection_id, "", context.messageHub, cancel_event):
                            return

                        chunks = []
                        if not context.parameters.settings.no_chunks:
                            chunks = Chunker().create_chunks_with_offsets(content, context.parameters.settings.chunk_type, context.parameters.settings.chunk_size, context.parameters.settings.chunk_overlap)
                        else:
                            chunks = [{"text": content, "start": 0}]

                        # delegate embedding + DB storage to helper
                        self._process_chunks_and_store(collection_id, file.source, "txt", chunks, context.parameters, context.messageHub, cancel_event)
                else:
                    print("File does not exist")
            finally:
                delete_file(context.db, file.id)
                TempFileHelper.remove_temp(file.path)
            
            
        
