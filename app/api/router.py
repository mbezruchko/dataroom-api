from fastapi import APIRouter
from app.api.routes import folders, files, search

api_router = APIRouter()

api_router.include_router(folders.router)
api_router.include_router(files.router)
api_router.include_router(search.router)