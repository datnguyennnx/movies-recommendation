from langfuse import Langfuse
from langfuse.callback import CallbackHandler
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

def initialize_langfuse():
    try:
        langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST
        )
        logger.info("Langfuse client initialized successfully")
        
        # Set up Langfuse callback handler
        callback_handler = CallbackHandler(langfuse_client=langfuse)
        
        return langfuse, callback_handler
    except Exception as e:
        logger.error(f"Error initializing Langfuse: {str(e)}", exc_info=True)
        return None, None

# Global Langfuse instance
langfuse, callback_handler = initialize_langfuse()

def get_langfuse():
    return langfuse

def get_callback_handler():
    return callback_handler

async def flush_langfuse():
    if langfuse:
        await langfuse.flush()
        logger.info("Langfuse client flushed successfully")