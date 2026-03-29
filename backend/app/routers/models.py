"""Model configuration routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.model_config import ModelConfig
from app.schemas.model_config import ModelConfigCreate, ModelConfigUpdate, ModelConfigRead
from app.utils.permissions import can_access_model

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/", response_model=list[ModelConfigRead])
async def list_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List accessible models for current user."""
    # Admins see all models
    from app.models.user import Role
    if current_user.role == Role.ADMIN:
        return db.query(ModelConfig).filter(ModelConfig.is_active).all()

    # Regular users see only models they have permission for
    models = db.query(ModelConfig).filter(ModelConfig.is_active).all()
    return [m for m in models if can_access_model(current_user.id, m.id, db)]


@router.post("/", response_model=ModelConfigRead, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelConfigCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a model config (admin only)."""
    model = ModelConfig(
        id=str(uuid.uuid4()),
        name=model_data.name,
        base_url=model_data.base_url,
        api_key=model_data.api_key,  # TODO: Encrypt with Fernet
        model_id=model_data.model_id,
        is_active=model_data.is_active
    )
    db.add(model)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Model name must be unique")
    db.refresh(model)
    return model


@router.get("/{model_id}", response_model=ModelConfigRead)
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a model config."""
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if not can_access_model(current_user.id, model_id, db):
        raise HTTPException(status_code=403, detail="Access denied")

    return model


@router.put("/{model_id}", response_model=ModelConfigRead)
async def update_model(
    model_id: str,
    update: ModelConfigUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a model config (admin only)."""
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if update.name:
        model.name = update.name
    if update.base_url:
        model.base_url = update.base_url
    if update.api_key:
        model.api_key = update.api_key  # TODO: Encrypt
    if update.model_id:
        model.model_id = update.model_id
    if update.is_active is not None:
        model.is_active = update.is_active

    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a model config (admin only)."""
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(model)
    db.commit()
    return {"message": "Model deleted"}
