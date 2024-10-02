from fastapi import APIRouter
from .ping import router as ping_router
from .config import router as config_router
from .websocket import router as websocket_router

api_router = APIRouter(prefix="/api")

routers = [
    ping_router,
    config_router,
    websocket_router
]

for router in routers:
    api_router.include_router(router)