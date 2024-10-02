import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from models.models import Conversation, Message, Movie, MovieFeature, UserViewingHistory, ModelEvaluation, ModelConfig
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def get_or_create_conversation(db: Session, user_id: str, model_config_id: str) -> Optional[Conversation]:
    try:
        # First, try to get an existing conversation
        existing_conversation = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.end_time.is_(None)
        ).first()
        if existing_conversation:
            return existing_conversation

        # If no existing conversation, create a new one
        conversation = Conversation(user_id=user_id, model_config_id=model_config_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    except SQLAlchemyError as e:
        logger.error(f"Error in get_or_create_conversation: {str(e)}")
        db.rollback()
        return None

def create_message(db: Session, conversation_id: str, role: str, content: str) -> Optional[Message]:
    try:
        message = Message(conversation_id=conversation_id, role=role, content=content)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    except SQLAlchemyError as e:
        logger.error(f"Error creating message: {str(e)}")
        db.rollback()
        return None

def classify_input(content: str) -> str:
    # Implement your classification logic here
    return "general"

def get_model_config(db_session: Session, user_id: str) -> Optional[ModelConfig]:
    """
    Get the current model configuration for a user.

    Args:
        db_session (Session): The database session.
        user_id (str): The ID of the user.

    Returns:
        Optional[ModelConfig]: The current model configuration, or None if not found.
    """
    try:
        stmt = select(ModelConfig).filter_by(user_id=user_id).order_by(ModelConfig.created_at.desc())
        return db_session.execute(stmt).scalars().first()
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_model_config: {str(e)}")
        return None

def store_model_evaluation(db: Session, model_config_id: str, model_name: str, conversation_id: str, metrics: Dict[str, float]) -> Optional[ModelEvaluation]:
    try:
        evaluation = ModelEvaluation(
            model_config_id=model_config_id,
            model_name=model_name,
            conversation_id=conversation_id,
            metrics=metrics
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation
    except SQLAlchemyError as e:
        logger.error(f"Error storing model evaluation: {str(e)}")
        db.rollback()
        return None

def get_movie_by_id(db: Session, movie_id: int) -> Optional[Movie]:
    try:
        return db.query(Movie).filter(Movie.id == movie_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving movie: {str(e)}")
        return None

def get_movie_features(db: Session, movie_id: int) -> Optional[List[float]]:
    try:
        movie_feature = db.query(MovieFeature).filter(MovieFeature.movie_id == movie_id).first()
        return movie_feature.features if movie_feature else None
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving movie features: {str(e)}")
        return None

def update_user_viewing_history(db: Session, user_id: str, movie_id: int) -> Optional[UserViewingHistory]:
    try:
        viewing_history = UserViewingHistory(user_id=user_id, movie_id=movie_id)
        db.add(viewing_history)
        db.commit()
        db.refresh(viewing_history)
        return viewing_history
    except SQLAlchemyError as e:
        logger.error(f"Error updating user viewing history: {str(e)}")
        db.rollback()
        return None

def get_user_viewing_history(db: Session, user_id: str, limit: int = 10) -> List[Movie]:
    try:
        return db.query(Movie).join(UserViewingHistory).filter(UserViewingHistory.user_id == user_id).order_by(UserViewingHistory.timestamp.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving user viewing history: {str(e)}")
        return []

# Add any other helper functions you need here
