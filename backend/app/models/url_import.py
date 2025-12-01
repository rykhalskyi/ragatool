from threading import Event
import time

import chromadb
from sentence_transformers import SentenceTransformer
from app.internal import simple_crawler
from app.internal.message_hub import MessageHub
from app.models.imports import ImportBase
from app.models.messages import MessageType
from app.schemas.imports import FileImportSettings, Import


class UrlImport(ImportBase):
    name = 'URL'


    @staticmethod
    def getDefault() -> Import:
        return Import(
            name="URL",
            model="all-MiniLM-L6-v2",
            settings=FileImportSettings(
                chunk_size=800,
                chunk_overlap=40,
                no_chunks=True
            )
        )
    
    async def import_data(self, collection_id: str, file_name: str, file_content_bytes: bytes, import_params: Import, message_hub:MessageHub, cancel_event: Event) -> None: # Modified signature
        message_hub.send_message(collection_id,  MessageType.LOCK, f"Starting import of {file_name}")
        message_hub.send_message(collection_id, MessageType.INFO, f"Crawling and parsing {file_name} ....")
        pages = simple_crawler.simple_crawl(file_name)

        message_hub.send_message(collection_id, MessageType.INFO, f"Parsed {len(pages)} pages")

        for page in pages:
            await self.__import_data_internal(collection_id, page["url"], page["text"], import_params, message_hub,cancel_event )

        message_hub.send_message(collection_id, MessageType.UNLOCK, f"Import of {file_name} completed.")

    async def __import_data_internal(self, collection_id: str, file_name: str, page_content: str, import_params: Import, message_hub:MessageHub, cancel_event: Event) -> None: # Modified signature
        try:
           
            chunks = []
            if not import_params.settings.no_chunks:
                chunks = self.create_chunks(page_content, import_params.settings.chunk_size, import_params.settings.chunk_overlap)
            else:
                chunks = [page_content]

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
                    f"{file_name}_{i}"
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
                
            message_hub.send_message(collection_id, MessageType.LOG, f"SUCCESSFUL imported from {file_name} {len(chunks)} chunks of length {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}.")
        except Exception as e:
            print("FAIL import_data", e)
            message_hub.send_message(collection_id, MessageType.LOG, f"FAILED import from {file_name}. Chunk size {import_params.settings.chunk_size}, overlap {import_params.settings.chunk_overlap}. Exception {e}")