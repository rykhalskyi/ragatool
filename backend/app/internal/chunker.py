from enum import Enum
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


class ChunkType(str, Enum):
    DEFAULT = "DEFAULT"
    RECURSIVE_CHARACTER = "RECURSIVE_CHARACTER"


class Chunker:
    def _validate(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

    def _chunk_default(self, text: str, chunk_size: int, chunk_overlap: int) -> List[dict]:
        self._validate(chunk_size, chunk_overlap)
        step = chunk_size - chunk_overlap
        return [
            {"text": text[i:i + chunk_size], "start": i}
            for i in range(0, len(text), step)
            if text[i:i + chunk_size]
        ]

    def _chunk_recursive(self, text: str, chunk_size: int, chunk_overlap: int) -> List[dict]:
        self._validate(chunk_size, chunk_overlap)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=DEFAULT_SEPARATORS,
            keep_separator=True,
            add_start_index=True,
        )
        docs = text_splitter.create_documents([text])
        return [
            {
                "text": doc.page_content,
                "start": doc.metadata.get("start_index", 0),
            }
            for doc in docs
        ]

    def create_chunks_with_offsets(
        self,
        text: str,
        chunk_type: ChunkType | None,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[dict]:
        """
        Returns chunks as {"text", "start"} records so callers can store
        character offsets alongside the chunk text.
        """
        match chunk_type:
            case ChunkType.RECURSIVE_CHARACTER:
                return self._chunk_recursive(text, chunk_size, chunk_overlap)
            case _:
                return self._chunk_default(text, chunk_size, chunk_overlap)

    def create_chunks(
        self,
        text: str,
        chunk_type: ChunkType | None,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[str]:
        return [
            chunk["text"]
            for chunk in self.create_chunks_with_offsets(
                text, chunk_type, chunk_size, chunk_overlap
            )
        ]
