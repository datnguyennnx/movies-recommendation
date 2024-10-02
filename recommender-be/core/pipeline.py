"""
This module contains the main pipeline for movie recommendations and a separate evaluation pipeline.
It includes integration with Langfuse for metric logging and tracing.
"""

import logging
from typing import AsyncGenerator, Dict, Union, Any, List
from sqlalchemy.orm import Session
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage
from models.models import User
from core.model_interface import BaseModelInterface
from core.agent.agent import MovieRecommendationAgent
from core.utils.helpers import (
    get_or_create_conversation,
    create_message,
    classify_input,
    get_model_config,
    store_model_evaluation,
)
from core.utils.prompts import create_memory_prompt, get_system_message
from core.evaluation.evaluator import evaluate_movie_recommendations
from langfuse.decorators import langfuse_context, observe
from config.langfuse_config import get_langfuse

logger = logging.getLogger(__name__)

# Get the Langfuse instance from the centralized config
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
def initialize_conversation(db_session: Session, user_id: str):
    logger.info(f"Initializing conversation for user_id: {user_id}")
    model_config = get_model_config(db_session, user_id)
    if model_config is None:
        logger.error(f"No model configuration found for user_id: {user_id}")
        raise ValueError(f"No model configuration found for user_id: {user_id}")
    
    logger.info(f"Model configuration found for user_id: {user_id}, model_config_id: {model_config.id}")
    conversation = get_or_create_conversation(db_session, user_id, str(model_config.id))
    if conversation is None:
        logger.error(f"Failed to create or retrieve conversation for user_id: {user_id}")
        raise ValueError(f"Failed to create or retrieve conversation for user_id: {user_id}")
    
    logger.info(f"Conversation initialized for user_id: {user_id}, conversation_id: {conversation.id}")
    return conversation.id

@observe()
def classify_user_input(content: str):
    return classify_input(content)

@observe()
async def retrieve_context(db_session: Session, user: User, content: str) -> AsyncGenerator[Dict[str, str], None]:
    agent = MovieRecommendationAgent(db_session, user)
    agent.initialize()
    context = {"recommendation": ""}
    async for token in agent.get_recommendation(content):
        context["recommendation"] += token
        yield {"type": "agent_thought", "content": token}
    yield {"type": "context", "content": context}

@observe()
def create_memory_prompt_step(chat_history, recommendation, content):
    return create_memory_prompt(chat_history, recommendation, content)

@observe()
def store_user_message(db_session: Session, conversation_id: str, content: str):
    create_message(db_session, conversation_id, "user", content)

@observe()
async def generate_model_response(model: BaseModelInterface, messages: List[Union[SystemMessage, HumanMessage]]) -> AsyncGenerator[Dict[str, str], None]:
    try:
        stream = await model.generate_stream(messages)
        async for token in stream:
            yield {"type": "final_response", "content": token}
    except Exception as e:
        logger.error(f"Error in generate_model_response: {str(e)}", exc_info=True)
        yield {"type": "error", "content": f"An error occurred: {str(e)}"}

@observe()
def store_assistant_message(db_session: Session, conversation_id: str, content: str):
    create_message(db_session, conversation_id, "assistant", content)

@observe()
def update_memory(memory: ConversationBufferMemory, user_message: str, ai_message: str):
    memory.chat_memory.add_user_message(user_message)
    memory.chat_memory.add_ai_message(ai_message)

def initialize_langfuse_trace(user_id: str, model_info: Dict[str, str]) -> Dict[str, Any]:
    if not is_langfuse_available():
        logger.warning("Langfuse is not available. Skipping trace initialization.")
        return {}

    try:
        trace = langfuse_context.update_current_trace(
            name="movie_recommendation",
            metadata={
                "user_id": user_id,
                "model_info": model_info
            }
        )
        trace_id = trace.id if trace else None
        span_id = langfuse_context.get_current_observation_id()

        if not trace_id or not span_id:
            logger.warning("Failed to obtain trace_id or span_id. Langfuse tracing might be unavailable.")
            return {}

        return {"trace_id": trace_id, "span_id": span_id}
    except Exception as e:
        logger.warning(f"Error initializing Langfuse trace: {str(e)}. Continuing without tracing.")
        return {}

@observe()
async def movie_recommendation_pipeline(
    data: Dict,
    db_session: Session,
    model: BaseModelInterface,
    memory: ConversationBufferMemory,
    user: User,
    session_id: str
) -> AsyncGenerator[Union[str, Dict[str, str]], None]:
    content = data.get('content', '')
    
    try:
        logger.info(f"Starting movie recommendation pipeline for user_id: {user.id}")
    
        logger.info(f"Retrieving model configuration for user_id: {user.id}")
        model_config = get_model_config(db_session, str(user.id))
        if model_config is None:
            logger.error(f"No model configuration found for user_id: {user.id}")
            raise ValueError(f"No model configuration found for user_id: {user.id}")
        logger.info(f"Model configuration retrieved for user_id: {user.id}, model_config_id: {model_config.id}")
        
        logger.info(f"Initializing conversation for user_id: {user.id}")
        conversation_id = initialize_conversation(db_session, str(user.id))
        logger.info(f"Conversation initialized for user_id: {user.id}, conversation_id: {conversation_id}")
        
        logger.info(f"Retrieving context for user_id: {user.id}")
        context = {"recommendation": ""}
        async for context_chunk in retrieve_context(db_session, user, content):
            if context_chunk["type"] == "context":
                context = context_chunk["content"]
            else:
                yield context_chunk
        logger.info(f"Context retrieved for user_id: {user.id}")
        
        chat_history = memory.chat_memory.messages
        recommendation = context["recommendation"]
        
        logger.info(f"Creating memory prompt for user_id: {user.id}")
        memory_prompt = create_memory_prompt_step(chat_history, recommendation, content)
        
        logger.info(f"Storing user message for user_id: {user.id}, conversation_id: {conversation_id}")
        store_user_message(db_session, str(conversation_id), content)
        
        system_message = SystemMessage(content=get_system_message())
        user_message = HumanMessage(content=memory_prompt + "\n\n Please respond to the user's query.")
        messages = [system_message, user_message]
        
        logger.info(f"Generating model response for user_id: {user.id}")
        complete_response = ""
        async for result in generate_model_response(model, messages):
            complete_response += result.get("content", "")
            yield result
        
        logger.info(f"Storing assistant message for user_id: {user.id}, conversation_id: {conversation_id}")
        store_assistant_message(db_session, str(conversation_id), complete_response)
        
        logger.info(f"Updating memory for user_id: {user.id}")
        update_memory(memory, content, complete_response)
        
        logger.info(f"Movie recommendation pipeline completed successfully for user_id: {user.id}")
        
        yield {"type": "end", "content": "# Pipeline completed\nMovie recommendation process finished."}

        evaluation_data = {
            "input": content,
            "recommendation_from_agent": recommendation,
            "conversation_response": complete_response,
            "db_session": db_session,
            "model_config_id": model_config.id if model_config else None,
            "model_name": model.model_name,
            "conversation_id": conversation_id
        }
        yield {
            "type": "evaluation_data",
            "content": evaluation_data
        }

        if is_langfuse_available():
            try:
                langfuse_context.update_current_observation(
                    output={
                        "status": "success",
                        "message": "Movie recommendation pipeline completed successfully",
                        "recommendation": recommendation
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to update Langfuse context: {str(e)}")

    except Exception as e:
        logger.error(f"Error in movie recommendation pipeline for user_id: {user.id}: {str(e)}", exc_info=True)
        error_message = f"I apologize, but I encountered an error while processing your message. Please try again later. Error: {str(e)}"
        yield {"type": "error", "content": f"# Error\n{error_message}"}
        if is_langfuse_available():
            try:
                langfuse_context.update_current_observation(
                    output={
                        "status": "error",
                        "message": error_message
                    },
                    level="ERROR"
                )
            except Exception as e:
                logger.warning(f"Failed to update Langfuse context with error: {str(e)}")

@observe()
async def evaluation_pipeline(pipeline_result: Dict):
    """
    Separate evaluation pipeline that can be called after the main pipeline.
    """
    try:
        logger.info("Starting evaluation pipeline")
        if not isinstance(pipeline_result, dict):
            logger.error(f"Invalid pipeline_result type: {type(pipeline_result)}")
            return {"type": "error", "content": "Invalid pipeline result format"}

        evaluation_data = pipeline_result
        if not evaluation_data:
            logger.error("Evaluation data is missing from pipeline result")
            return {"type": "error", "content": "Evaluation data is missing from pipeline result"}

        # Ensure recommendation_from_agent is a string
        if not isinstance(evaluation_data.get('recommendation_from_agent'), str):
            logger.warning(f"Unexpected recommendation_from_agent type: {type(evaluation_data.get('recommendation_from_agent'))}")
            evaluation_data['recommendation_from_agent'] = str(evaluation_data.get('recommendation_from_agent', ''))

        evaluation_result = await evaluate_movie_recommendations(evaluation_data)

        if evaluation_result:
            result = {
                "type": "evaluation",
                "content": evaluation_result.dict() if hasattr(evaluation_result, 'dict') else evaluation_result
            }
            
            # Log the evaluation result
            logger.info(f"Evaluation result: {result}")
            
            if is_langfuse_available():
                try:
                    langfuse_context.update_current_observation(
                        name="evaluation_pipeline",
                        output=result
                    )
                except Exception as e:
                    logger.warning(f"Failed to update Langfuse context with evaluation result: {str(e)}")
            
            # Store the evaluation result in the database
            metrics = result["content"].get("metrics", {}) if isinstance(result["content"], dict) else {}
            store_model_evaluation(
                evaluation_data.get("db_session"),
                evaluation_data.get("model_config_id"),
                evaluation_data.get("model_name"),
                evaluation_data.get("conversation_id"),
                metrics
            )
            
            logger.info("Evaluation pipeline completed successfully")
            return result
        else:
            logger.warning("Evaluation failed or returned no results")
            error_result = {"type": "error", "content": "Evaluation failed or returned no results"}
            if is_langfuse_available():
                try:
                    langfuse_context.update_current_observation(
                        name="evaluation_pipeline",
                        output=error_result,
                        level="ERROR"
                    )
                except Exception as e:
                    logger.warning(f"Failed to update Langfuse context with error: {str(e)}")
            return error_result
    except Exception as e:
        logger.error(f"Error in evaluation pipeline: {str(e)}", exc_info=True)
        error_result = {"type": "error", "content": f"An error occurred during evaluation: {str(e)}"}
        return error_result
