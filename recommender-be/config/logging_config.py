import logging
import os
from logging.handlers import RotatingFileHandler

def configure_logging():
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure root logger
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # Create a rotating file handler
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, 'movie_recommender.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Get the root logger and add the file handler
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Configure specific loggers
    logging.getLogger('openai').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('core.movie_recommendation_pipeline').setLevel(logging.DEBUG)
    logging.getLogger('core.agent').setLevel(logging.DEBUG)
    logging.getLogger('routes.api.websocket').setLevel(logging.DEBUG)
    logging.getLogger('core.askLLM').setLevel(logging.DEBUG)  # Add this line

    # Add any other relevant loggers here

configure_logging()