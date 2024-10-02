import logging
from typing import Dict, Any, List, Union
from langchain.schema import HumanMessage 
from core.model_interface import OpenAIModel
from config.settings import settings
from core.utils.prompts import get_evaluation_prompt
from config.langfuse_config import get_langfuse
import re
import json
from langfuse.decorators import langfuse_context, observe
from models.models import ModelEvaluation, Conversation, ModelConfig
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

# Get the Langfuse instance from the centralized config
langfuse = get_langfuse()

class EvaluationResult:
    def __init__(self, metrics: Dict[str, float], comments: Dict[str, str]):
        self.metrics = metrics
        self.comments = comments

    def dict(self):
        return {
            "metrics": self.metrics,
            "comments": self.comments
        }

class MovieRecommendationEvaluator:
    def __init__(self):
        self.model = OpenAIModel(model_name="gpt-4-1106-preview", api_key=settings.OPENAI_API_KEY)

    @observe()
    async def evaluate_run(self, data: Dict[str, Any]) -> EvaluationResult:
        try:
            logger.info("Starting evaluation run")
            trace_id = data.get("trace_id")
            span_id = data.get("span_id")
            
            if not trace_id or not span_id:
                logger.warning("trace_id or span_id is missing in the input data")

            recommendation_from_agent = data.get("recommendation_from_agent", [])
            conversation_response = data.get("conversation_response", "")
            user_input = data.get("input", "")

            logger.debug(f"User input: {user_input}")
            logger.debug(f"Recommendation from agent type: {type(recommendation_from_agent)}")
            logger.debug(f"Recommendation from agent: {recommendation_from_agent}")
            logger.debug(f"Conversation response: {conversation_response}")

            # Convert recommendation_from_agent to a list of strings if it's not already
            if isinstance(recommendation_from_agent, str):
                recommendation_from_agent = [recommendation_from_agent]
            elif not isinstance(recommendation_from_agent, list):
                recommendation_from_agent = [str(recommendation_from_agent)]

            formatted_recommendations = self._format_movies(recommendation_from_agent[:5])
            prompt = get_evaluation_prompt(user_input, formatted_recommendations, conversation_response)

            logger.debug(f"Evaluation prompt: {prompt}")

            messages = [HumanMessage(content=prompt)]
            response = await self.model.generate(messages)

            logger.debug(f"Raw model response: {response}")

            scores = self._extract_scores(response)
            
            comments = {}
            for score_name, score_value in scores.items():
                comments[score_name] = f"{score_name.capitalize()} Score: {score_value:.2f}"
                self._log_score_to_langfuse(score_name, score_value, trace_id, span_id)
                logger.info(f"Logged score to Langfuse: {score_name} = {score_value:.2f}")
            
            logger.info("Evaluation run completed successfully")
            return EvaluationResult(metrics=scores, comments=comments)
        except Exception as e:
            logger.error(f"Error in evaluate_run: {str(e)}", exc_info=True)
            return EvaluationResult(metrics={}, comments={"error": str(e)})

    def _format_movies(self, movies: List[Union[Dict[str, Any], str]]) -> str:
        """Helper method to format movie information"""
        formatted_movies = []
        for movie in movies:
            if isinstance(movie, dict):
                title = movie.get('title', '')
                release_date = movie.get('release_date', '')
                year = release_date[:4] if release_date else ''
                overview = movie.get('overview', '')
                formatted_movies.append(f"{title} ({year}): {overview}")
            elif isinstance(movie, str):
                formatted_movies.append(movie)
            else:
                logger.warning(f"Unexpected movie format: {type(movie)}")
                formatted_movies.append(str(movie))
        return "\n".join(formatted_movies)

    def _extract_scores(self, response: str) -> Dict[str, float]:
        try:
            scores_match = re.search(r'\[SCORES\](.*?)\[/SCORES\]', response, re.DOTALL)
            if scores_match:
                scores_text = scores_match.group(1)
                scores = {}
                for line in scores_text.strip().split('\n'):
                    key, value = line.split(':')
                    scores[key.strip()] = float(value.strip())

                # Ensure all scores are between 0 and 1
                for key in scores:
                    scores[key] = max(0.0, min(1.0, scores[key]))

                logger.debug(f"Extracted scores: {scores}")
                return scores
            else:
                raise ValueError("Scores not found in the expected format")
        except Exception as e:
            logger.error(f"Error extracting scores: {str(e)}")
            logger.error(f"Full response: {response}")
            return {
                "relevance": 0.0,
                "diversity": 0.0,
                "clarity": 0.0,
                "personalization": 0.0,
                "conciseness": 0.0,
                "coherence": 0.0,
                "helpfulness": 0.0,
                "harmfulness": 0.0,
                "overall": 0.0
            }

    def _log_score_to_langfuse(self, score_name: str, score_value: float, trace_id: str, span_id: str):
        try:
            langfuse_context.score_current_observation(
                name=score_name,
                value=score_value,
                comment=f"{score_name.capitalize()} Score: {score_value:.2f}"
            )
        except Exception as e:
            logger.error(f"Error logging score to Langfuse: {str(e)}")

@observe()
async def evaluate_movie_recommendations(data: Dict[str, Any]) -> EvaluationResult:
    logger.info("Starting movie recommendation evaluation")
    trace_id = data.get("trace_id")
    span_id = data.get("span_id")
    conversation_id = data.get("conversation_id")
    db_session = data.get("db_session")

    if not trace_id or not span_id:
        logger.warning("trace_id or span_id is missing in the input data")

    if not isinstance(db_session, Session):
        logger.error("Invalid db_session provided")
        return EvaluationResult(metrics={}, comments={"error": "Invalid database session"})

    try:
        try:
            langfuse_context.update_current_observation(
                name="evaluate_movie_recommendations",
                input={
                    "user_input": data.get("input", ""),
                    "recommendation": data.get("recommendation_from_agent", []),
                    "conversation_response": data.get("conversation_response", "")
                },
                metadata={"model_name": "gpt-4-1106-preview"}
            )
        except Exception as e:
            logger.warning(f"Failed to update Langfuse context: {str(e)}")

        evaluator = MovieRecommendationEvaluator()
        result = await evaluator.evaluate_run(data)
        logger.info("Movie recommendation evaluation completed")
        logger.debug(f"Evaluation result: {result.dict()}")

        try:
            langfuse_context.update_current_observation(
                output=result.dict()
            )
        except Exception as e:
            logger.warning(f"Failed to update Langfuse context with result: {str(e)}")

        # Store evaluation results in the database
        if conversation_id:
            conversation = db_session.query(Conversation).get(conversation_id)
            if conversation:
                model_config = conversation.model_config
                try:
                    evaluation = ModelEvaluation(
                        model_config_id=model_config.id,
                        model_name=model_config.model,
                        conversation_id=conversation_id,
                        metrics=result.metrics
                    )
                    db_session.add(evaluation)
                    db_session.commit()
                    logger.info(f"Evaluation stored for conversation_id: {conversation_id}")
                except IntegrityError as ie:
                    logger.error(f"IntegrityError while storing evaluation: {str(ie)}")
                    db_session.rollback()
                    # If an evaluation already exists, update it instead
                    existing_evaluation = db_session.query(ModelEvaluation).filter_by(conversation_id=conversation_id).first()
                    if existing_evaluation:
                        existing_evaluation.metrics = result.metrics
                        db_session.commit()
                        logger.info(f"Existing evaluation updated for conversation_id: {conversation_id}")
                    else:
                        logger.error("Failed to store or update evaluation")
            else:
                logger.warning(f"Conversation with id {conversation_id} not found")
        else:
            logger.warning("No conversation_id provided, skipping evaluation storage")

        return result
    except Exception as e:
        logger.error(f"Error in evaluate_movie_recommendations: {str(e)}", exc_info=True)
        error_result = EvaluationResult(metrics={}, comments={"error": str(e)})
        try:
            langfuse_context.update_current_observation(
                output=error_result.dict(),
                level="ERROR"
            )
        except Exception as le:
            logger.warning(f"Failed to update Langfuse context with error: {str(le)}")
        return error_result
