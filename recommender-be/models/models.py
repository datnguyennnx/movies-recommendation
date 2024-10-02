from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, Text, DateTime, func, ARRAY, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

# Association tables
movie_genre = Table('movie_genre', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id')),
    Column('genre_id', Integer, ForeignKey('genres.id'))
)

movie_actor = Table('movie_actor', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id')),
    Column('actor_id', Integer, ForeignKey('actors.id'))
)

class Movie(Base):
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    budget = Column(Integer)
    genres_data = Column(Text)  # We'll store this as JSON string
    homepage = Column(String)
    keywords = Column(Text)  # We'll store this as JSON string
    original_language = Column(String)
    original_title = Column(String)
    overview = Column(Text)
    popularity = Column(Float)
    production_companies = Column(Text)  # We'll store this as JSON string
    release_date = Column(String)
    revenue = Column(Integer)
    runtime = Column(Integer)
    status = Column(String)
    tagline = Column(String)
    vote_average = Column(Float)
    vote_count = Column(Integer)
    
    # Fields from credits.csv
    cast = Column(Text)  # We'll store this as JSON string
    crew = Column(Text)  # We'll store this as JSON string

    director_id = Column(Integer, ForeignKey('directors.id'))
    director = relationship("Director", back_populates="movies")

    genres = relationship("Genre", secondary=movie_genre, back_populates="movies")
    actors = relationship("Actor", secondary=movie_actor, back_populates="movies")
    features = relationship("MovieFeature", back_populates="movie", uselist=False)

class MovieFeature(Base):
    __tablename__ = 'movie_features'

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'), unique=True)
    features = Column(ARRAY(Float))  # Store feature vector as an array of floats

    movie = relationship("Movie", back_populates="features")

class Genre(Base):
    __tablename__ = 'genres'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    
    movies = relationship("Movie", secondary=movie_genre, back_populates="genres")

class Actor(Base):
    __tablename__ = 'actors'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    
    movies = relationship("Movie", secondary=movie_actor, back_populates="actors")

class Director(Base):
    __tablename__ = 'directors'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    
    movies = relationship("Movie", back_populates="director")

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    picture = Column(String, nullable=True)
    timezone = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    sessions = relationship("Session", back_populates="user")
    model_configs = relationship("ModelConfig", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    viewing_history = relationship("UserViewingHistory", back_populates="user")

class Session(Base):
    __tablename__ = 'sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    client_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")

class ModelConfig(Base):
    __tablename__ = 'model_configs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    api_key = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="model_configs")
    evaluations = relationship("ModelEvaluation", back_populates="model_config")

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    model_config_id = Column(UUID(as_uuid=True), ForeignKey('model_configs.id'), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    langfuse_trace_id = Column(String(255), nullable=True)

    user = relationship("User", back_populates="conversations")
    model_config = relationship("ModelConfig")
    messages = relationship("Message", back_populates="conversation")
    evaluation = relationship("ModelEvaluation", back_populates="conversation", uselist=False)

class Message(Base):
    __tablename__ = 'messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")

class UserViewingHistory(Base):
    __tablename__ = 'user_viewing_history'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="viewing_history")
    movie = relationship("Movie")

class ModelEvaluation(Base):
    __tablename__ = 'model_evaluations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_config_id = Column(UUID(as_uuid=True), ForeignKey('model_configs.id'), nullable=False)
    model_name = Column(String(100), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
    metrics = Column(JSON, nullable=False)  # Store all evaluation metrics as a JSON object
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    model_config = relationship("ModelConfig", back_populates="evaluations")
    conversation = relationship("Conversation", back_populates="evaluation")
