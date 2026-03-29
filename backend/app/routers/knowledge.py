"""Knowledge/RAG routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.knowledge import KnowledgeCollection, KnowledgeDocument, DocumentStatus
from app.schemas.knowledge import CollectionCreate, CollectionRead, DocumentCreate, DocumentRead
from app.utils.permissions import can_access_collection
from app.services.document_service import process_document

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/", response_model=list[CollectionRead])
async def list_collections(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List knowledge collections."""
    from app.models.user import Role
    if current_user.role == Role.ADMIN:
        return db.query(KnowledgeCollection).offset(skip).limit(limit).all()

    # Regular users: only their collections or public ones
    collections = db.query(KnowledgeCollection).filter(
        KnowledgeCollection.created_by == current_user.id
    ).offset(skip).limit(limit).all()
    return collections


@router.post("/", response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a knowledge collection."""
    # Create Chroma collection
    chroma_name = f"collection_{uuid.uuid4().hex[:8]}"

    collection = KnowledgeCollection(
        id=str(uuid.uuid4()),
        name=collection_data.name,
        chroma_collection_name=chroma_name,
        created_by=current_user.id
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


@router.get("/{collection_id}", response_model=CollectionRead)
async def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a knowledge collection."""
    collection = db.query(KnowledgeCollection).filter(
        KnowledgeCollection.id == collection_id
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not can_access_collection(current_user.id, collection_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    return collection


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a knowledge collection."""
    collection = db.query(KnowledgeCollection).filter(
        KnowledgeCollection.id == collection_id
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(collection)
    db.commit()
    return {"message": "Collection deleted"}


@router.post("/{collection_id}/documents", response_model=DocumentRead)
async def add_document(
    collection_id: str,
    doc_data: DocumentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a document to a collection (async processing)."""
    collection = db.query(KnowledgeCollection).filter(
        KnowledgeCollection.id == collection_id
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create document record
    doc = KnowledgeDocument(
        id=str(uuid.uuid4()),
        collection_id=collection_id,
        file_id=doc_data.file_id,
        title=doc_data.title or "Document",
        status=DocumentStatus.PENDING
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Queue async processing
    # background_tasks.add_task(process_document, doc.id, file_path, content_type, collection.chroma_collection_name, db=db)

    return doc


@router.delete("/{collection_id}/documents/{doc_id}")
async def delete_document(
    collection_id: str,
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document from a collection."""
    collection = db.query(KnowledgeCollection).filter(
        KnowledgeCollection.id == collection_id
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.collection_id == collection_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}
