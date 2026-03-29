"""Text chunking utilities for RAG."""
import tiktoken
from typing import List


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks based on token count.

    Args:
        text: Text to split
        chunk_size: Target size in tokens per chunk
        overlap: Number of tokens to overlap between chunks

    Returns:
        List of text chunks
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)

    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)

        # Move start forward, accounting for overlap
        start = end - overlap

    return chunks


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in text."""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
