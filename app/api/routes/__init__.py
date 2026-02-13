"""
API 路由模块
"""
from fastapi import APIRouter
from app.api.routes import chat, system_instruction, auth

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(system_instruction.router)

__all__ = ["api_router"]
