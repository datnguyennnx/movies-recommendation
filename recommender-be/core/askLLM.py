from typing import Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session
from core.pipeline import movie_recommendation_pipeline, evaluation_pipeline
from core.model_interface import BaseModelInterface
from langchain.memory import ConversationBufferMemory
from models.models import User
import logging
import json
from langfuse.decorators import observe, langfuse_context
from config.langfuse_config import get_langfuse

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

def extract_token_usage(response):
    """
    Extract token usage information from the model's response.
    """
    if hasattr(response, 'usage'):
        return {
            "input_tokens": getattr(response.usage, 'input_tokens', 0),
            "output_tokens": getattr(response.usage, 'output_tokens', 0),
            "total_tokens": getattr(response.usage, 'total_tokens', 0)
        }
    return {}

@observe(as_type="generation", capture_input=False, capture_output=False)
async def askLLM(
    data: Dict[str, Any],
    db_session: Session,
    model: BaseModelInterface,
    memory: ConversationBufferMemory,
    user: User,
    session_id: str
) -> AsyncGenerator[Dict[str, Any], None]:
    logger.debug(f"Input data: {json.dumps(data, default=str)}")

    if is_langfuse_available():
        try:
            input_data = {
                "data": data,
                "user_id": str(user.id),
                "session_id": session_id,
                "model_info": {
                    "provider": model.__class__.__name__,
                    "model_name": model.model_name
                }
            }
            logger.debug(f"Langfuse input data: {json.dumps(input_data, default=str)}")
            langfuse_context.update_current_observation(
                name="askLLM",
                input=input_data,
                metadata={"model_name": model.model_name}
            )
        except Exception as e:
            logger.error(f"Error updating Langfuse observation: {str(e)}", exc_info=True)

    try:
        evaluation_data = None
        pipeline_metadata = {
            "steps": [],
            "recommendations": [],
            "evaluation": None,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        }
        
        async for response_chunk in movie_recommendation_pipeline(data, db_session, model, memory, user, session_id):
            logger.debug(f"Response chunk: {json.dumps(response_chunk, default=str)}")
            if isinstance(response_chunk, dict):
                response_type = response_chunk.get("type")
                if response_type in ["final_response", "agent_thought", "error", "end"]:
                    yield response_chunk
                    pipeline_metadata["steps"].append({
                        "type": response_type,
                        "content": response_chunk.get("content"),
                        "timestamp": response_chunk.get("timestamp")
                    })
                    # Update token usage if available
                    token_usage = extract_token_usage(response_chunk.get("raw_response", {}))
                    for key in token_usage:
                        pipeline_metadata["token_usage"][key] += token_usage[key]
                elif response_type == "evaluation_data":
                    evaluation_data = response_chunk.get("content")
                    if "recommendations" in evaluation_data:
                        pipeline_metadata["recommendations"] = evaluation_data["recommendations"]
                else:
                    logger.warning(f"Unexpected response type: {response_type}")
                    yield response_chunk
                    pipeline_metadata["steps"].append({
                        "type": "unknown",
                        "content": str(response_chunk),
                        "timestamp": response_chunk.get("timestamp")
                    })
            else:
                logger.warning(f"Unexpected response chunk: {str(response_chunk)}")
                pipeline_metadata["steps"].append({
                    "type": "unknown",
                    "content": str(response_chunk),
                    "timestamp": None
                })
        
        if evaluation_data:
            evaluation_result = await run_evaluation_pipeline(evaluation_data, model.model_name)
            if evaluation_result:
                yield evaluation_result
                pipeline_metadata["evaluation"] = evaluation_result

        if is_langfuse_available():
            try:
                output_data = {
                    "status": "success",
                    "message": "Movie recommendation and evaluation pipeline completed successfully",
                    "pipeline_metadata": pipeline_metadata
                }
                logger.debug(f"Langfuse output data: {json.dumps(output_data, default=str)}")
                langfuse_context.update_current_observation(
                    output=output_data,
                    usage=pipeline_metadata["token_usage"]
                )
            except Exception as e:
                logger.error(f"Error updating Langfuse observation: {str(e)}", exc_info=True)
        
    except Exception as e:
        logger.error(f"Error in askLLM: {str(e)}", exc_info=True)
        error_message = f"An error occurred: {str(e)}"
        yield {"type": "error", "content": error_message}
        
        if is_langfuse_available():
            try:
                error_output = {
                    "status": "error",
                    "message": error_message,
                    "pipeline_metadata": pipeline_metadata
                }
                logger.debug(f"Langfuse error output data: {json.dumps(error_output, default=str)}")
                langfuse_context.update_current_observation(
                    output=error_output,
                    usage=pipeline_metadata["token_usage"]
                )
            except Exception as le:
                logger.error(f"Error updating Langfuse observation: {str(le)}", exc_info=True)

@observe(name="movie_recommendation_evaluation", capture_input=False, capture_output=False)
async def run_evaluation_pipeline(pipeline_result: Dict, model_name: str):
    try:
        evaluation_result = await evaluation_pipeline(pipeline_result)
        
        if is_langfuse_available() and langfuse:
            try:
                # Log individual scores
                for score_name, score_value in evaluation_result.get("content", {}).get("metrics", {}).items():
                    logger.debug(f"Logging score to Langfuse: {score_name} = {score_value}")
                    langfuse.score(
                        trace_id=pipeline_result.get("trace_id"),
                        span_id=pipeline_result.get("span_id"),
                        name=score_name,
                        value=score_value,
                        comment=f"{score_name.capitalize()} score from recommendation evaluation"
                    )
                    logger.info(f"Logged score to Langfuse: {score_name} = {score_value}")

                # Log the full evaluation result as an observation
                logger.debug(f"Logging evaluation result to Langfuse: {json.dumps(evaluation_result, default=str)}")
                langfuse_context.update_current_observation(
                    name="evaluation_pipeline",
                    input=pipeline_result,
                    output=evaluation_result,
                    metadata={"model_name": model_name}
                )
            except Exception as e:
                logger.error(f"Error logging to Langfuse: {str(e)}", exc_info=True)
        
        return evaluation_result
    except Exception as e:
        logger.error(f"Error in run_evaluation_pipeline: {str(e)}", exc_info=True)
        error_message = f"An error occurred during evaluation: {str(e)}"
        
        if is_langfuse_available():
            try:
                error_output = {
                    "status": "error",
                    "message": error_message
                }
                logger.debug(f"Langfuse evaluation error output: {json.dumps(error_output, default=str)}")
                langfuse_context.update_current_observation(
                    name="evaluation_pipeline",
                    input=pipeline_result,
                    output=error_output,
                    metadata={"model_name": model_name}
                )
            except Exception as le:
                logger.error(f"Error updating Langfuse observation for evaluation error: {str(le)}", exc_info=True)
        
        return {"type": "error", "content": error_message}
