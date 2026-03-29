"""Prompt management routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptRead

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("/", response_model=list[PromptRead])
async def list_prompts(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List prompts (own + public)."""
    from sqlalchemy import or_
    return db.query(Prompt).filter(
        or_(
            Prompt.user_id == current_user.id,
            Prompt.is_public == True
        )
    ).offset(skip).limit(limit).all()


@router.post("/", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_data: PromptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a prompt."""
    prompt = Prompt(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=prompt_data.title,
        content=prompt_data.content,
        is_public=prompt_data.is_public
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}", response_model=PromptRead)
async def get_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a prompt."""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if prompt.user_id != current_user.id and not prompt.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    return prompt


@router.put("/{prompt_id}", response_model=PromptRead)
async def update_prompt(
    prompt_id: str,
    update: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a prompt."""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt or prompt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if update.title:
        prompt.title = update.title
    if update.content:
        prompt.content = update.content
    if update.is_public is not None:
        prompt.is_public = update.is_public

    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a prompt."""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt or prompt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(prompt)
    db.commit()
    return {"message": "Prompt deleted"}
