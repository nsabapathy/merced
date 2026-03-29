"""RAG (Retrieval-Augmented Generation) service."""
from sqlalchemy.orm import Session
from app.services.chroma_service import chroma_service
from app.models.knowledge import KnowledgeCollection, DocumentStatus
from app.config import settings


async def embed_query(query: str, api_key: str, base_url: str = "https://api.openai.com") -> list[float]:
    """Embed a query using OpenAI embedding API."""
    import httpx

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "text-embedding-3-small",
        "input": query
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/v1/embeddings",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


async def retrieve_context(
    collection_name: str,
    query_embedding: list[float],
    top_k: int = None
) -> list[str]:
    """Retrieve relevant documents from a collection."""
    if top_k is None:
        top_k = settings.rag_top_k

    try:
        results = await chroma_service.query(
            collection_name=collection_name,
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        if results and "documents" in results and results["documents"]:
            return results["documents"][0]
    except Exception:
        pass

    return []


def build_system_context(documents: list[str]) -> str:
    """Build system context from retrieved documents."""
    if not documents:
        return ""

    context = "You have access to the following information:\n\n"
    for i, doc in enumerate(documents, 1):
        context += f"[{i}] {doc}\n\n"

    context += "Use the above information to answer the user's question if relevant.\n"
    return context


async def prepare_rag_context(
    query: str,
    knowledge_collection_id: str,
    embedding_api_key: str,
    db: Session
) -> str:
    """Prepare RAG context for a query."""
    # Get the collection
    collection = db.query(KnowledgeCollection).filter(
        KnowledgeCollection.id == knowledge_collection_id
    ).first()

    if not collection:
        return ""

    # Get indexed documents count
    indexed_count = db.query(KnowledgeCollection).filter(
        KnowledgeCollection.id == knowledge_collection_id
    ).first()

    if not indexed_count:
        return ""

    try:
        # Embed the query
        query_embedding = await embed_query(query, embedding_api_key)

        # Retrieve relevant documents
        documents = await retrieve_context(
            collection.chroma_collection_name,
            query_embedding
        )

        # Build system context
        return build_system_context(documents)
    except Exception:
        return ""
