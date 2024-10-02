from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    FRONTEND_URL: str
    SECRET_KEY: str
    DATABASE_URL: str
    OPENAI_API_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    COOKIE_SECURE: bool = False  # Set to True in production with HTTPS

    # New WebSocket settings
    WEBSOCKET_KEEPALIVE_TIMEOUT: int = 60  # Default 60 seconds
    WEBSOCKET_PONG_TIMEOUT: int = 10  # Default 10 seconds
    WEBSOCKET_RECEIVE_TIMEOUT: int = 60  # Default 60 seconds
    
    # Langfuse settings
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    EVALUATION_THRESHOLDS: float = 0.5

    class Config:
        env_file = ".env"

settings = Settings()