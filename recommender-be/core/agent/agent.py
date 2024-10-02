import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.models import User, ModelConfig, Conversation, Message, ModelEvaluation
from core.model_interface import ModelFactory
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langfuse.decorators import observe, langfuse_context
from config.langfuse_config import get_langfuse
import json
from typing import Dict, Any, List, AsyncGenerator, Tuple, Optional

from core.utils.prompts import get_chain_of_thought_system_message

logger = logging.getLogger(__name__)

# Get the Langfuse instance from the centralized config
langfuse = get_langfuse()

class MovieRecommendationAgent:
    def __init__(self, db: Session, user: User):
        logger.info("Initializing MovieRecommendationAgent with database session")
        self.db = db
        self.user = user
        self.config = None
        self.model = None
        self.memory = ConversationBufferWindowMemory(k=5)  # Retain only the last 5 interactions
        self.langfuse = langfuse

    def is_langfuse_available(self):
        try:
            return (self.langfuse is not None and 
                    hasattr(langfuse_context, 'current_observation') and 
                    langfuse_context.current_observation is not None)
        except Exception as e:
            logger.warning(f"Error checking Langfuse availability: {str(e)}")
            return False

    @observe()
    def initialize(self):
        try:
            self.config = self._get_user_config()
            self.model = self._initialize_model()
        except Exception as e:
            logger.error(f"Error initializing MovieRecommendationAgent: {str(e)}", exc_info=True)
            raise

    @observe()
    def _get_user_config(self) -> ModelConfig:
        config = self.db.query(ModelConfig).filter(ModelConfig.user_id == self.user.id).first()
        if config:
            logger.info(f"User config found: provider={config.provider}, model={config.model}")
        else:
            logger.warning(f"No model configuration found for user {self.user.id}")
        return config

    @observe()
    def _initialize_model(self):
        if self.config:
            try:
                model = ModelFactory.create_model(
                    provider=self.config.provider,
                    model_name=self.config.model, 
                    api_key=self.config.api_key,
                )
                logger.info(f"Model initialized for provider: {self.config.provider}")
                return model
            except Exception as e:
                logger.error(f"Error initializing model: {str(e)}", exc_info=True)
                raise
        else:
            logger.error("User has not configured a model")
            raise ValueError("User has not configured a model")

    @observe()
    def _execute_query(self, query: text, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            result = self.db.execute(query, params)
            result_list = []
            for row in result:
                if hasattr(row, '_asdict'):
                    # If row is a SQLAlchemy RowProxy
                    result_list.append(row._asdict())
                elif isinstance(row, dict):
                    # If row is already a dictionary
                    result_list.append(row)
                else:
                    # If row is neither a RowProxy nor a dict, try to convert it
                    try:
                        result_list.append(dict(row))
                    except Exception as e:
                        logger.warning(f"Could not convert row to dictionary: {e}")
                        continue
            
            if not result_list:
                logger.warning("Query returned no results")
            
            return result_list
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            raise

    def _classify_query(self, question: str) -> List[str]:
        question = question.lower()
        query_types = []

        classification_rules = [
            ('financial', ['budget', 'revenue', 'profit', 'box office', 'earnings', 'cost', 'gross', 'net', 'financial', 'money']),
            ('popularity', ['popular', 'rating', 'vote', 'liked', 'favorite', 'trending', 'well-received', 'acclaimed', 'hit']),
            ('genre', ['genre', 'category', 'type', 'kind of movie', 'style of film']),
            ('actor', ['actor', 'star', 'cast', 'performer', 'actress']),
            ('director', ['director', 'filmmaker', 'directed by', 'helmed by']),
            ('release_date', ['release', 'year', 'when', 'came out', 'debut', 'premiered']),
            ('plot', ['plot', 'story', 'about', 'synopsis', 'narrative', 'storyline']),
            ('recommendation', ['recommend', 'suggest', 'similar', 'like', 'comparable', 'akin to']),
            ('awards', ['award', 'oscar', 'golden globe', 'emmy', 'nominated', 'won']),
            ('language', ['language', 'spoken in', 'subtitle', 'dub']),
            ('duration', ['duration', 'length', 'how long', 'runtime']),
            ('production', ['production company', 'studio', 'produced by']),
            ('franchise', ['franchise', 'series', 'sequel', 'prequel']),
            ('theme', ['theme', 'message', 'moral', 'underlying']),
            ('cinematography', ['cinematography', 'visuals', 'shot', 'filmed']),
            ('soundtrack', ['soundtrack', 'music', 'score', 'composer'])
        ]

        for query_type, keywords in classification_rules:
            if any(keyword in question for keyword in keywords):
                query_types.append(query_type)
        
        if not query_types:
            query_types.append("general")

        return query_types

    def _extract_limit(self, question: str) -> int:
        match = re.search(r'top\s+(\d+)|(\d+)\s+(actors|movies|films|results)', question, re.IGNORECASE)
        if match:
            return int(next(group for group in match.groups() if group is not None))
        return 5  # Default limit if no number is found

    def _extract_name(self, question: str) -> Optional[str]:
        # Simple regex to match names (assuming names are capitalized words)
        name_match = re.search(r'\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)\b', question)
        if name_match:
            return name_match.group(1)
        return None

    @observe()
    def _build_query(self, query_types: List[str], question: str) -> Tuple[text, Dict[str, Any]]:
        limit = self._extract_limit(question)
        
        base_query = f"""
        SELECT DISTINCT m.id, m.title, m.overview, m.budget, m.revenue, m.popularity, 
               m.vote_average, m.vote_count, m.release_date, m.keywords,
               string_agg(DISTINCT g.name, ', ') as genres,
               (SELECT string_agg(name, ', ')
                FROM (SELECT DISTINCT a.name 
                      FROM movie_actor ma 
                      JOIN actors a ON ma.actor_id = a.id 
                      WHERE ma.movie_id = m.id 
                      ORDER BY a.name 
                      LIMIT :actor_limit) AS top_actors
               ) as top_actors,
               d.name as director
        FROM movies m
        LEFT JOIN movie_genre mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        LEFT JOIN movie_actor ma ON m.id = ma.movie_id
        LEFT JOIN actors a ON ma.actor_id = a.id
        LEFT JOIN directors d ON m.director_id = d.id
        WHERE 1=1
        """

        conditions = []
        order_by = []
        params = {"actor_limit": limit}

        if "financial" in query_types:
            if 'high budget' in question:
                conditions.append("m.budget > 0")
                order_by.append("m.budget DESC")
            elif 'low budget' in question:
                conditions.append("m.budget > 0")
                order_by.append("m.budget ASC")
            elif 'high revenue' in question:
                conditions.append("m.revenue > 0")
                order_by.append("m.revenue DESC")
            elif 'low revenue' in question:
                conditions.append("m.revenue > 0")
                order_by.append("m.revenue ASC")
            elif 'profit' in question:
                conditions.append("m.revenue > 0 AND m.budget > 0")
                order_by.append("(m.revenue - m.budget) DESC")
            else:
                order_by.append("m.revenue DESC")

        if "popularity" in query_types:
            if 'rating' in question or 'vote' in question:
                order_by.extend(["m.vote_average DESC", "m.vote_count DESC"])
            elif 'trending' in question:
                order_by.extend(["m.popularity DESC", "m.release_date DESC"])
            else:
                order_by.append("m.popularity DESC")

        if "genre" in query_types:
            genres = ['Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family', 
                      'Fantasy', 'History', 'Horror', 'Music', 'Mystery', 'Romance', 'Science Fiction', 
                      'TV Movie', 'Thriller', 'War', 'Western']
            
            genre_conditions = []
            for i, genre in enumerate(genres):
                if genre.lower() in question.lower():
                    genre_conditions.append(f"LOWER(g.name) = :genre_{i}")
                    params[f"genre_{i}"] = genre.lower()
            
            if genre_conditions:
                conditions.append("(" + " OR ".join(genre_conditions) + ")")

        if "actor" in query_types:
            actor_name = self._extract_name(question)
            if actor_name:
                conditions.append("LOWER(a.name) LIKE LOWER(:actor_name)")
                params["actor_name"] = f"%{actor_name}%"

        if "director" in query_types:
            director_name = self._extract_name(question)
            if director_name:
                conditions.append("LOWER(d.name) LIKE LOWER(:director_name)")
                params["director_name"] = f"%{director_name}%"

        if "release_date" in query_types:
            year_match = re.search(r'\b(19|20)\d{2}\b', question)
            if year_match:
                year = year_match.group()
                conditions.append("EXTRACT(YEAR FROM m.release_date) = :year")
                params["year"] = int(year)
            elif 'recent' in question or 'latest' in question:
                conditions.append("m.release_date >= (CURRENT_DATE - INTERVAL '2 years')")
                order_by.append("m.release_date DESC")
            elif 'old' in question or 'classic' in question:
                conditions.append("EXTRACT(YEAR FROM m.release_date) < 1980")
                order_by.append("m.release_date ASC")

        if "awards" in query_types:
            conditions.append("m.keywords::text LIKE '%award%' OR m.keywords::text LIKE '%nominated%'")

        if "language" in query_types:
            lang_match = re.search(r'in ([\w\s]+)', question)
            if lang_match:
                lang = lang_match.group(1).strip().lower()
                conditions.append("LOWER(m.original_language) = :lang")
                params["lang"] = lang

        if "duration" in query_types:
            if 'short' in question:
                conditions.append("m.runtime <= 90")
            elif 'long' in question:
                conditions.append("m.runtime >= 150")

        if "franchise" in query_types:
            conditions.append("m.keywords::text LIKE '%sequel%' OR m.keywords::text LIKE '%series%'")

        # Add conditions to base query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        # Add search terms for general queries
        search_terms = [term.lower() for term in question.split() if len(term) > 2]
        if search_terms:
            search_condition = " OR ".join([
                f"LOWER(m.title) LIKE :term_{i} OR LOWER(m.overview) LIKE :term_{i} OR LOWER(m.keywords::text) LIKE :term_{i}"
                for i in range(len(search_terms))
            ])
            base_query += f" AND ({search_condition})"
            for i, term in enumerate(search_terms):
                params[f"term_{i}"] = f"%{term}%"

        # Add GROUP BY clause
        base_query += " GROUP BY m.id, d.name"

        # Add ORDER BY clause
        if order_by:
            base_query += " ORDER BY " + ", ".join(order_by)
        else:
            base_query += " ORDER BY m.popularity DESC"

        base_query += f" LIMIT :result_limit"
        params["result_limit"] = limit

        return text(base_query), params

    @observe()
    def retrieve_data(self, question: str) -> Dict[str, Any]:
        logger.info(f"Retrieving data for question: {question}")
        try:
            query_types = self._classify_query(question)
            query, params = self._build_query(query_types, question)
            results = self._execute_query(query, params)
            
            return {
                "results": results,
                "raw_query": query.text,
                "query_types": query_types
            }
        except Exception as e:
            logger.error(f"Error in retrieve_data: {str(e)}", exc_info=True)
            raise

    @observe()
    async def chain_of_thought(self, question: str) -> AsyncGenerator[str, None]:
        logger.info(f"Starting chain of thought for question: {question}")
        
        try:
            # Retrieve data
            retrieved_data = self.retrieve_data(question)
            
            # Get the raw query from the retrieved data
            raw_query = retrieved_data.get("raw_query", "No query available")
            
            # Get the system message
            system_message_content = get_chain_of_thought_system_message()
            
            # Ensure system_message_content is a string
            if isinstance(system_message_content, list):
                system_message_content = "\n".join(system_message_content)
            elif not isinstance(system_message_content, str):
                system_message_content = str(system_message_content)
            
            chat_history = self.memory.chat_memory.messages
            
            prompt = f"""
            Question: {question}

            Retrieved Data:
            ```json
            {json.dumps(retrieved_data, indent=2)}
            ```

            Raw Query:
            ```sql
            {raw_query}
            ```

            Please provide your analysis, recommendation, and response based on the given question, retrieved data, and raw query.
            Structure your response to include:
            1. Thought Process: Explain your reasoning based on the query and data.
            2. Data Analysis: Analyze the retrieved data and its relevance to the question.
            3. Query Analysis: Discuss the SQL query used and its appropriateness for the question.
            4. Recommendation: Provide movie recommendations based on the analysis.
            5. Raw query: Provide raw query in block code with SQL tag.

            If no results were found, provide suggestions for refining the search or alternative questions the user could ask.
            """
            
            messages = [
                SystemMessage(content=system_message_content),
                *chat_history,
                HumanMessage(content=prompt)
            ]
            
            try:
                stream = await self.model.generate_stream(messages)
                async for token in stream:
                    yield token
            except Exception as e:
                logger.error(f"Error in generate_stream: {str(e)}", exc_info=True)
                yield f"An error occurred while generating the response: {str(e)}"

            self.memory.chat_memory.add_user_message(question)
            self.memory.chat_memory.add_ai_message("Recommendation provided.")

        except Exception as e:
            logger.error(f"Error in chain_of_thought: {str(e)}", exc_info=True)
            yield "I apologize, but I encountered an unexpected error while processing your request. Please try again later or rephrase your question."

    @observe()
    async def get_recommendation(self, question: str) -> AsyncGenerator[str, None]:
        logger.info(f"Getting recommendation for question: {question}")
        
        try:
            self.initialize()
            async for token in self.chain_of_thought(question):
                yield token
        
        except Exception as e:
            logger.error(f"Error in get_recommendation: {str(e)}", exc_info=True)
            yield "I apologize, but an error occurred while processing your request. Please try again later or contact support if the problem persists."

    @observe()
    def store_conversation(self, user_input: str, ai_response: str) -> None:
        try:
            conversation = Conversation(
                user_id=self.user.id,
                model_config_id=self.config.id,
                langfuse_trace_id=langfuse_context.current_observation.trace_id if self.is_langfuse_available() else None
            )
            self.db.add(conversation)
            self.db.flush()  # This will assign an ID to the conversation

            user_message = Message(conversation_id=conversation.id, role='user', content=user_input)
            ai_message = Message(conversation_id=conversation.id, role='assistant', content=ai_response)
            
            self.db.add(user_message)
            self.db.add(ai_message)
            self.db.commit()

            logger.info(f"Stored conversation with ID: {conversation.id}")
        except Exception as e:
            logger.error(f"Error storing conversation: {str(e)}", exc_info=True)
            self.db.rollback()

    @observe()
    def store_evaluation(self, conversation_id: str, metrics: Dict[str, float]) -> None:
        try:
            evaluation = ModelEvaluation(
                model_config_id=self.config.id,
                model_name=self.config.model,
                conversation_id=conversation_id,
                metrics=metrics
            )
            self.db.add(evaluation)
            self.db.commit()

            logger.info(f"Stored evaluation for conversation ID: {conversation_id}")
        except Exception as e:
            logger.error(f"Error storing evaluation: {str(e)}", exc_info=True)
            self.db.rollback()
