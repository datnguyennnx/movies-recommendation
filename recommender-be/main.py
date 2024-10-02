import os
import logging
from routes.main import create_app
from config.settings import settings
import asyncio
from config.langfuse_config import get_langfuse, get_callback_handler, flush_langfuse
from config.logging_config import configure_logging

# Set up logging
configure_logging()
logger = logging.getLogger(__name__)

app = create_app()
app.title = "Backend Recommender"
app.debug = False

def is_langfuse_available(langfuse, callback_handler):
    return langfuse is not None and callback_handler is not None

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup initiated")
    
    try:
        # Initialize Langfuse client and callback handler
        langfuse = get_langfuse()
        callback_handler = get_callback_handler()
        
        if is_langfuse_available(langfuse, callback_handler):
            logger.info("Langfuse client and callback handler initialized successfully")
            # Store the callback_handler and langfuse client in the app state for later use
            app.state.callback_handler = callback_handler
            app.state.langfuse = langfuse
            
            # Test Langfuse connection
            try:
                # Create a test trace
                trace = langfuse.trace("test_trace")
                logger.info(f"Test Langfuse trace created with ID: {trace.id}")
                # End the test trace
                trace.end()
                logger.info("Langfuse connection test successful")
            except Exception as le:
                logger.error(f"Langfuse connection test failed: {str(le)}", exc_info=True)
        else:
            logger.warning("Failed to initialize Langfuse client or callback handler")

        # Perform any async initialization tasks here
        await asyncio.sleep(0)  # Example of an async operation

        logger.info("Application startup complete")
        for route in app.routes:
            logger.info(f"Registered route: {route.path}")

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        # Consider raising an exception here if the error is critical

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown initiated")
    
    try:
        # Flush Langfuse client
        if hasattr(app.state, 'langfuse') and app.state.langfuse is not None:
            await flush_langfuse()
            logger.info("Langfuse client flushed successfully")
        else:
            logger.warning("No Langfuse client to flush")

        # Perform any async cleanup tasks here
        await asyncio.sleep(0)  # Example of an async operation

        logger.info("Application shutdown complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)

if __name__ == "__main__":
    import uvicorn
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=log_level)