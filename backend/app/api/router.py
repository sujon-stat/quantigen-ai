from fastapi import APIRouter
from backend.app.api.endpoints import datasets, methods, analysis, chat, export, power, registry

api_router = APIRouter()

api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(methods.router, prefix="/methods", tags=["methods"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(power.router, prefix="/power", tags=["power"])
api_router.include_router(registry.router, prefix="/registry", tags=["registry"])
