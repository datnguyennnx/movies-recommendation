from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from db.database import get_db
from models.models import User, ModelConfig
from routes.auth.google import verify_token
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/configure-model")
async def configure_model(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        provider = data.get("provider")
        model = data.get("model")
        api_key = data.get("apiKey")
        token = request.cookies.get("token")

        logger.info(f"Received configuration request: provider={provider}, model={model}")

        if not all([provider, model, api_key, token]):
            raise HTTPException(status_code=400, detail="Missing required parameters")

        user_info = verify_token(token, db)
        if not user_info or not user_info.get("valid"):
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.info(f"User info: {user_info}")

        user_id = user_info['user']['sub']
        logger.info(f"User ID: {user_id}")

        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user ID format")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        config = db.query(ModelConfig).filter(ModelConfig.user_id == user_id).first()
        if config:
            config.provider = provider
            config.model = model
            config.api_key = api_key
        else:
            config = ModelConfig(user_id=user_id, provider=provider, model=model, api_key=api_key)
            db.add(config)

        db.commit()
        return {"message": "Model configuration saved successfully"}
    except Exception as e:
        logger.error(f"Error configuring model: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error configuring model: {str(e)}")

@router.get("/model-config")
async def get_model_config(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    user_info = verify_token(token, db)
    if not user_info or not user_info.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")

    logger.info(f"User info: {user_info}")

    user_id = user_info['user']['sub']
    logger.info(f"User ID: {user_id}")

    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    config = db.query(ModelConfig).filter(ModelConfig.user_id == user_id).first()
    if not config:
        return {"provider": "", "model": "", "message": "Model not configured. Please configure the model."}

    return {"provider": config.provider, "model": config.model}