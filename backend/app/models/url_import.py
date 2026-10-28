import os
from threading import Event
import time

import numpy as np
from app.crud.crud_files import create_file, delete_file, get_files_for_collection
from app.internal import simple_crawler, vector_store
from app.internal.chunker import Chunker, ChunkType
from app.internal.embedding_manager import (
    DEFAULT_EMBEDDING_MODEL,
    embed_documents,
    resolve_embedding_model,
)
from app.internal.message_hub import MessageHub
from app.internal.temp_file_helper import TempFileHelper
from app.models.import_context import ImportContext
from app.models.imports import ImportBase
from app.models.messages import MessageType
from app.schemas.imports import FileImportSettings, Import
from app.schemas.setting import SettingsName

import re


class UrlImport(ImportBase):
    name = 'URL'

    @staticmethod
    def getDefault() -> Import:
        return Import(
            name="URL",
            model=DEFAULT_EMBEDDING_MODEL,
            settings=FileImportSettings(
                chunk_size=800,
                chunk_overlap=80,
                no_chunks=False,
                chunk_type=ChunkType.RECURSIVE_CHARACTER
            )
        )
    
    async def prepare_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, message_hub: MessageHub) -> str:
         extracted_text = file_content_bytes.decode("utf-8")
         return extracted_text
    
    async def import_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, context: ImportContext, cancel_event: Event) -> None: # Modified signature
        message_hub = context.messageHub
        import_params = context.parameters
        
        message_hub.send_message(collection_id,  MessageType.LOCK, f"Starting import of {file_name}")
        message_hub.send_message(collection_id, MessageType.INFO, f"Crawling and parsing {file_name} ....")
        
        max_depth = context.settings.get_setting_int(SettingsName.CRAWL_DEPTH, 1)

        compiled_regex = None
        if context.parameters.settings.filter:
            try:
                compiled_regex = re.compile(context.parameters.settings.filter)
            except re.error:
                # Invalid regex, ignore it
                pass
            
        pages = simple_crawler.simple_crawl(file_name, cancel_event, compiled_regex, max_depth=max_depth)

        if pages == None:
             message_hub.send_message(collection_id, MessageType.LOG, f"NOTHING imported from {file_name}. Parsed no pages.")
             return

        message_hub.send_message(collection_id, MessageType.INFO, f"Parsed {len(pages)} pages")

        for page in pages:
            if cancel_event.is_set():
                 message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} was cancelled")
                 message_hub.send_message(collection_id, MessageType.LOG, f"CANCELLED Import from {file_name} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.") 
                 return
            
            if compiled_regex and not compiled_regex.match(page["url"]):
                continue
            
            await self.__import_data_internal(collection_id, page["url"], page["text"], import_params, message_hub,cancel_event )

        message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} completed.")

    async def __import_data_internal(self, collection_id: str, file_name: str, page_content: str, import_params: Import, message_hub:MessageHub, cancel_event: Event) -> None: # Modified signature
        try:
           
            chunks = []
            if not import_params.settings.no_chunks:
                chunks = Chunker().create_chunks_with_offsets(page_content, import_params.settings.chunk_type, import_params.settings.chunk_size, import_params.settings.chunk_overlap)
            else:
                chunks = [{"text": page_content, "start": 0}]

            message_hub.send_message(collection_id, MessageType.INFO, f"Created {len(chunks)} chunks. Embedding....")

            client = vector_store.get_client()
            try:
                collection = client.get_collection(name=collection_id)
                embedding_model = vector_store.get_collection_embedding_model(collection)
            except Exception:
                embedding_model = resolve_embedding_model(import_params.model)
                collection = vector_store.get_or_create_collection(
                    collection_id, embedding_model=embedding_model, client=client
                )

            embeddings = np.array(list(embed_documents([chunk["text"] for chunk in chunks], embedding_model)))
            message_hub.send_message(collection_id, MessageType.INFO, "Embeddings created. Saving to Database....")

            if cancel_event.is_set():
                 message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} was cancelled")
                 message_hub.send_message(collection_id, MessageType.LOG, f"CANCELLED Import from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
                 return

            ts = int(time.time())
            # ---- batching logic ----
            max_batch_size = 5000  # safe limit below Chroma's 5461 cap

            batch_num = 1
            for start in range(0, len(chunks), max_batch_size):
                if cancel_event.is_set():
                    message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} was cancelled")
                    message_hub.send_message(collection_id, MessageType.LOG, f"CANCELLED Import from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
                    return

                end = start + max_batch_size

                batch_records = chunks[start:end]
                batch_embeddings = embeddings[start:end].tolist()

                batch_ids = [
                    f"{file_name}_{i}"
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
                
            message_hub.send_message(collection_id, MessageType.LOG, f"SUCCESSFUL imported from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
        except Exception as e:
            print("FAIL import_data", e)
            message_hub.send_message(collection_id, MessageType.LOG, f"FAILED import from {file_name}. Chunk size {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}. Exception {e}")


    async def step_1(self, collection_id: str, url: str, context: ImportContext, cancel_event:Event) -> None: # Modified signature
        if not context.settings.check(SettingsName.TWO_STEP_IMPORT, 'True'):
            context.messageHub.send_message(collection_id, MessageType.INFO, "Set 2 Step mode to use this function")
            return

        context.messageHub.send_message(collection_id,  MessageType.LOCK, f"Starting import of {url}")
        context.messageHub.send_message(collection_id, MessageType.INFO, f"Crawling and parsing {url} ....")
        
        max_depth = context.settings.get_setting_int(SettingsName.CRAWL_DEPTH, 1)

        compiled_regex = None
        if context.parameters.settings.filter:
            try:
                compiled_regex = re.compile(context.parameters.settings.filter)
            except re.error:
                # Invalid regex, ignore it
                pass    
        
        pages = simple_crawler.simple_crawl(url, cancel_event, compiled_regex, max_depth=max_depth)

        if pages == None:
             context.messageHub.send_message(collection_id, MessageType.LOG, f"NOTHING imported from {url}. Parsed no pages.")
             return

        context.messageHub.send_message(collection_id, MessageType.INFO, f"Parsed {len(pages)} pages")

        for page in pages:
            if cancel_event.is_set():
                 context.messageHub.send_message(collection_id, MessageType.UNLOCK, f"Import of {url} was cancelled")
                 context.messageHub.send_message(collection_id, MessageType.LOG, f"CANCELLED Import from {url} chunks of length {context.parameters.settings.chunk_size}, overlap {context.parameters.settings.chunk_overlap}.") 
                 return
            
            if compiled_regex and not compiled_regex.match(page["url"]):
                continue
            
            print('Match', page["url"])
            tmp_file = TempFileHelper.save_temp_str(page["text"], page["url"])
            create_file(context.db, collection_id, tmp_file, page["url"])
            
            
        context.messageHub.send_message(collection_id, MessageType.UNLOCK, f"Import of {url} completed.")


def read_file_lines(file_path: str) -> list[str]:
    """
    Read a text file and return a list of strings, one per line.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        List of strings, each representing one line from the file
    """
    with open(file_path, 'r') as file:
        return [line.rstrip('\n') for line in file]