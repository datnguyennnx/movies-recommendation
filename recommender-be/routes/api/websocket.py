from fastapi import APIRouter, Depends, WebSocket, Query, status
from sqlalchemy.orm import Session
from db.database import get_db
from models.models import User, ModelConfig
from routes.auth.google import verify_token
import logging
from core.model_interface import ModelFactory
from langchain.memory import ConversationBufferMemory
from config.settings import settings
from starlette.websockets import WebSocketState, WebSocketDisconnect
from datetime import datetime
import pytz
import json
import asyncio
from core.askLLM import askLLM
import uuid
from langfuse.decorators import observe, langfuse_context
from config.langfuse_config import get_langfuse

router = APIRouter()
logger = logging.getLogger(__name__)

langfuse = get_langfuse()

def is_langfuse_available():
    try:
        return (langfuse is not None and 
                hasattr(langfuse_context, 'current_observation') and 
                langfuse_context.current_observation is not None)
    except Exception as e:
        logger.warning(f"Error checking Langfuse availability: {str(e)}")
        return False

@observe()
def convert_timestamp(timestamp_str: str, user_timezone: str = 'UTC') -> tuple:
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        else:
            dt = dt.astimezone(pytz.utc)
        user_tz = pytz.timezone(user_timezone)
        local_dt = dt.astimezone(user_tz)
        return dt.isoformat(), local_dt.isoformat()
    except Exception as e:
        logger.error(f"Error converting timestamp: {str(e)}")
        return timestamp_str, timestamp_str  # Return original timestamp if conversion fails

@observe(as_type="generation")
async def process_user_message(data: dict, db: Session, model, memory, user: User, session_id: str):
    """Process a user message and return the AI response with tracing information."""
    message_id = str(uuid.uuid4())
    try:
        async for response_chunk in askLLM(data, db, model, memory, user, session_id):
            if isinstance(response_chunk, dict):
                response_type = response_chunk.get("type", "token")
                if response_type in ["agent_thought", "final_response", "error", "end", "evaluation"]:
                    yield {
                        "message_id": message_id if response_type != "evaluation" else str(uuid.uuid4()),
                        "content": response_chunk.get("content", ""),
                        "type": response_type,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                else:
                    logger.warning(f"Unexpected response type: {response_type}")
                    yield {
                        "message_id": message_id,
                        "content": str(response_chunk),
                        "type": "unknown",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
            else:
                logger.warning(f"Unexpected response chunk type: {type(response_chunk)}")
                yield {
                    "message_id": message_id,
                    "content": str(response_chunk),
                    "type": "unknown",
                    "timestamp": datetime.utcnow().isoformat(),
                }

    except Exception as e:
        logger.error(f"Error in process_user_message: {str(e)}", exc_info=True)
        yield {
            "message_id": message_id,
            "content": f"An error occurred: {str(e)}",
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
        }

async def close_websocket(websocket: WebSocket):
    """Close the websocket connection."""
    if websocket.client_state == WebSocketState.CONNECTED:
        await websocket.close()
    logger.info("WebSocket connection closed")

@observe()
@router.websocket("/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    await websocket.accept()
    logger.info(f"WebSocket connection attempt with token: {token[:10]}...")

    user = None
    config = None
    model = None
    memory = None
    session_id = str(uuid.uuid4())  # Generate a unique session ID for this WebSocket connection

    try:
        if not token:
            logger.warning("No token provided, closing WebSocket connection")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_info = verify_token(token, db)
        logger.info(f"Token verification result: {user_info}")

        if not user_info or not user_info.get("valid"):
            logger.warning(f"Invalid token, user_info: {user_info}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user = db.query(User).filter(User.id == uuid.UUID(user_info['user']['sub'])).first()
        if not user:
            logger.warning(f"User not found for sub: {user_info['user']['sub']}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        logger.info(f"Authenticated user: {user.email}")

        config = db.query(ModelConfig).filter(ModelConfig.user_id == user.id).order_by(ModelConfig.created_at.desc()).first()
        if not config:
            logger.warning("No model configuration found for user")
            await websocket.send_json({"type": "error", "content": "No model configuration found"})
            await websocket.close()
            return

        try:
            model = ModelFactory.create_model(config.provider, config.model, config.api_key)
            logger.info(f"Model created: {config.provider} - {config.model}")
        except ValueError as e:
            logger.error(f"Error creating model: {str(e)}")
            await websocket.send_json({"type": "error", "content": str(e)})
            await websocket.close()
            return

        memory = ConversationBufferMemory()
        logger.info("ConversationBufferMemory initialized")

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=settings.WEBSOCKET_RECEIVE_TIMEOUT)
                logger.info(f"Received message: {data}")

                @observe(capture_input=False, capture_output=False, )
                async def message():
                    if is_langfuse_available():
                        try:
                            # Set the session ID for this trace
                            langfuse_context.update_current_trace(
                                session_id=session_id,
                                metadata={
                                        "provider": config.provider,
                                        "model": config.model
                                }
                            )
                        except Exception as e:
                            logger.error(f"Error updating Langfuse trace: {str(e)}", exc_info=True)

                    if 'timestamp' in data:
                        utc_timestamp, local_timestamp = convert_timestamp(data['timestamp'], user.timezone)
                        if utc_timestamp and local_timestamp:
                            data['utc_timestamp'] = utc_timestamp
                            data['local_timestamp'] = local_timestamp
                        else:
                            logger.error("Failed to convert timestamp")

                    output_metadata = {}
                    async for response in process_user_message(data, db, model, memory, user, session_id):
                        if websocket.client_state == WebSocketState.CONNECTED:
                            await websocket.send_json(response)
                            output_metadata[response["message_id"]] = {
                                "type": response["type"],
                                "timestamp": response["timestamp"]
                            }
                        else:
                            logger.warning("WebSocket disconnected during message processing")
                            return

                    if is_langfuse_available():
                        try:
                            langfuse_context.update_current_observation(
                                output={
                                    "responses": output_metadata
                                }
                            )
                        except Exception as e:
                            logger.error(f"Error updating Langfuse observation: {str(e)}", exc_info=True)

                await message()

            except asyncio.TimeoutError:
                logger.info("Receive timeout, continuing...")
                continue
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({"type": "error", "content": "Invalid JSON format"})
            except Exception as e:
                logger.error(f"Error while processing message: {str(e)}", exc_info=True)
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "message_id": str(uuid.uuid4()),
                        "content": f"An unexpected error occurred: {str(e)}",
                        "type": "error",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    await websocket.send_json({"type": "end"})

    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}", exc_info=True)
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json({
                "message_id": str(uuid.uuid4()),
                "content": f"WebSocket error: {str(e)}",
                "type": "error",
                "timestamp": datetime.utcnow().isoformat(),
            })
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    finally:
        logger.info("Closing WebSocket connection")
        await close_websocket(websocket)

        if is_langfuse_available():
            try:
                # End the Langfuse trace for this session
                langfuse_context.end_trace(session_id)
                logger.info(f"Langfuse trace ended for session: {session_id}")
            except Exception as e:
                logger.error(f"Error ending Langfuse trace: {str(e)}", exc_info=True)