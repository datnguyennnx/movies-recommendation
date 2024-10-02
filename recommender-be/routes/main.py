from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import api_router
from .auth import auth_router
from config.settings import settings

def create_app():
    app = FastAPI()

    app.add_middleware(
           CORSMiddleware,
           allow_origins=[
               settings.FRONTEND_URL,
               "http://localhost",
               "http://localhost:80",
               "http://frontend:3000",
               "ws://localhost",
               "ws://localhost:80",
           ],
           allow_credentials=True,
           allow_methods=["*"],
           allow_headers=["*"],
       )

    # Include API router
    app.include_router(api_router)

    # Include Google authentication router
    app.include_router(auth_router)

    return app