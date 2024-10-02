from fastapi import APIRouter
from .google import router as google_router

auth_router = APIRouter(prefix="/auth")

routers = [
    google_router 
]

for router in routers:
    auth_router.include_router(router)