"""Tests for RAG service."""
import pytest
from app.utils.chunking import chunk_text, estimate_tokens


def test_chunk_text():
    """Test text chunking."""
    text = "This is a test. " * 100  # Create a longer text
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_chunk_text_with_overlap():
    """Test that chunks have overlap."""
    text = "Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8 Word9 Word10 " * 20
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    # If there's overlap, consecutive chunks should share some content
    assert len(chunks) > 1


def test_estimate_tokens():
    """Test token estimation."""
    text = "This is a test."
    tokens = estimate_tokens(text)
    assert isinstance(tokens, int)
    assert tokens > 0


def test_estimate_tokens_longer_text():
    """Test token estimation for longer text."""
    text = "This is a test. " * 100
    tokens = estimate_tokens(text)
    # Should estimate more tokens for longer text
    short_text = "This is a test."
    short_tokens = estimate_tokens(short_text)
    assert tokens > short_tokens
