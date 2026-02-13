"""
聊天服务
处理聊天逻辑（无数据库版本）
"""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_instruction import SystemInstruction
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.litellm_service import litellm_service

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务类 - 处理聊天业务逻辑（无数据库存储）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_system_instruction_by_id(self, instruction_id: int) -> Optional[str]:
        """根据 ID 获取系统提示词"""
        result = await self.db.execute(
            select(SystemInstruction).where(SystemInstruction.id == instruction_id)
        )
        instruction = result.scalar_one_or_none()
        return instruction.content if instruction else None

    async def _get_default_system_instruction(self) -> Optional[str]:
        """获取默认的系统提示词"""
        result = await self.db.execute(
            select(SystemInstruction)
            .where(SystemInstruction.is_default == True)
            .order_by(SystemInstruction.sort_order)
            .limit(1)
        )
        instruction = result.scalar_one_or_none()
        return instruction.content if instruction else None

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        处理聊天请求（无数据库存储版本）

        Args:
            request: 聊天请求，包含 messages 列表（对话上下文）

        Returns:
            聊天响应
        """
        # 1. 获取系统提示词（优先级：直接传入 > 指定ID > 默认值）
        system_instruction_content = None
        if request.system_instruction:
            # 用户直接传入系统提示词
            system_instruction_content = request.system_instruction
        elif request.system_instruction_id:
            # 通过 ID 获取
            system_instruction_content = await self._get_system_instruction_by_id(request.system_instruction_id)
        else:
            # 使用默认值
            system_instruction_content = await self._get_default_system_instruction()

        # 2. 构建消息列表
        # 将前端传入的对话上下文转换为 litellm 格式
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        # 3. 调用 LLM
        response = await litellm_service.chat_completion(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_instruction=system_instruction_content,
            prompt=None,  # 不再使用 prompt
        )

        # 4. 提取回复内容和使用情况
        assistant_content = litellm_service.extract_message_content(response)
        usage_info = litellm_service.extract_usage(response)

        # 5. 构建响应（无数据库操作）
        return ChatResponse(
            message=assistant_content,
            usage=usage_info,
        )
