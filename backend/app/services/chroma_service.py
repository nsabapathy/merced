"""Chroma vector database service."""
import httpx
import uuid
from typing import Optional
from app.config import settings


class ChromaService:
    """Chroma HTTP client wrapper."""

    def __init__(self):
        self.base_url = settings.chroma_url

    async def create_collection(self, name: str) -> dict:
        """Create a new collection."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/collections",
                json={"name": name}
            )
            response.raise_for_status()
            return response.json()

    async def get_collection(self, name: str) -> dict:
        """Get a collection by name."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/collections/{name}"
            )
            response.raise_for_status()
            return response.json()

    async def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/v1/collections/{name}"
            )
            response.raise_for_status()

    async def upsert(self, collection_name: str, documents: list[str],
                     embeddings: list[list[float]], ids: list[str],
                     metadatas: Optional[list[dict]] = None) -> None:
        """Upsert documents to a collection."""
        async with httpx.AsyncClient() as client:
            payload = {
                "documents": documents,
                "embeddings": embeddings,
                "ids": ids
            }
            if metadatas:
                payload["metadatas"] = metadatas

            response = await client.post(
                f"{self.base_url}/api/v1/collections/{collection_name}/upsert",
                json=payload
            )
            response.raise_for_status()

    async def query(self, collection_name: str, query_embeddings: list[list[float]],
                    n_results: int = 5) -> dict:
        """Query a collection."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/collections/{collection_name}/query",
                json={
                    "query_embeddings": query_embeddings,
                    "n_results": n_results
                }
            )
            response.raise_for_status()
            return response.json()

    async def delete_documents(self, collection_name: str, ids: list[str]) -> None:
        """Delete documents from a collection."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/collections/{collection_name}/delete",
                json={"ids": ids}
            )
            response.raise_for_status()


chroma_service = ChromaService()
