from enum import Enum
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

class ChunkType(str, Enum):
    DEFAULT = "DEFAULT"
    RECURSIVE_CHARACTER = "RECURSIVE_CHARACTER"

class Chunker:
    def _chunk_default(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]

    def _chunk_recursive(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        return text_splitter.split_text(text)

    def create_chunks(self, text: str, chunk_type: ChunkType | None, chunk_size: int, chunk_overlap: int) -> List[str]:
        match chunk_type:
            case ChunkType.RECURSIVE_CHARACTER:
                return self._chunk_recursive(text, chunk_size, chunk_overlap)
            case _:
                return self._chunk_default(text, chunk_size, chunk_overlap)
