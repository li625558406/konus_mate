"""
API 依赖注入模块
定义 FastAPI 的依赖项
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.chat_service import ChatService
from app.services.system_instruction_service import SystemInstructionService
from app.services.prompt_service import PromptService


async def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """获取聊天服务实例"""
    return ChatService(db)


async def get_system_instruction_service(db: AsyncSession = Depends(get_db)) -> SystemInstructionService:
    """获取系统提示词服务实例"""
    return SystemInstructionService(db)


async def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptService:
    """获取 Prompt 服务实例"""
    return PromptService(db)
