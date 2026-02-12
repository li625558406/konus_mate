"""
聊天服务
处理聊天逻辑和数据存储
"""
import logging
import uuid
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import ChatSession, ChatMessage
from app.models.system_instruction import SystemInstruction
from app.models.prompt import Prompt
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageResponse, ChatSessionResponse
from app.services.litellm_service import litellm_service

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务类 - 处理聊天业务逻辑"""

    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def _get_default_prompt(self) -> Optional[str]:
        """获取默认的 prompt"""
        result = await self.db.execute(
            select(Prompt)
            .where(Prompt.is_default == True)
            .order_by(Prompt.sort_order)
            .limit(1)
        )
        prompt = result.scalar_one_or_none()
        return prompt.content if prompt else None

    async def _get_session_messages(self, session_id: str, limit: int = 20) -> List[ChatMessage]:
        """获取会话历史消息"""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def chat(self, request: ChatRequest, user_id: str = "default_user") -> ChatResponse:
        """
        处理聊天请求

        Args:
            request: 聊天请求
            user_id: 用户ID

        Returns:
            聊天响应
        """
        session_id = request.session_id
        system_instruction_content = None
        prompt_content = None

        # 获取系统提示词
        if request.system_instruction_id:
            result = await self.db.execute(
                select(SystemInstruction).where(SystemInstruction.id == request.system_instruction_id)
            )
            instruction = result.scalar_one_or_none()
            if instruction:
                system_instruction_content = instruction.content
        else:
            system_instruction_content = await self._get_default_system_instruction()

        # 获取 prompt
        if request.prompt_id:
            result = await self.db.execute(
                select(Prompt).where(Prompt.id == request.prompt_id)
            )
            prompt_obj = result.scalar_one_or_none()
            if prompt_obj:
                prompt_content = prompt_obj.content
        else:
            prompt_content = await self._get_default_prompt()

        # 创建或获取会话
        if not session_id:
            session_id = str(uuid.uuid4())
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
                system_instruction_id=request.system_instruction_id,
                prompt_id=request.prompt_id,
            )
            self.db.add(session)
            await self.db.flush()

        # 保存用户消息
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message,
            system_instruction_id=request.system_instruction_id,
            prompt_id=request.prompt_id,
        )
        self.db.add(user_message)
        await self.db.flush()

        # 构建消息历史 - 加载会话的历史消息实现多轮对话
        messages = []

        # 加载历史消息（最近的 20 条）
        history = await self._get_session_messages(session_id, limit=20)

        # 将历史消息转换为 litellm 格式
        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": request.message
        })

        # 限制历史消息数量，避免 token 超限
        # 只保留最近的 15 条消息（约 7-8 轮对话）
        if len(messages) > 15:
            messages = messages[-15:]

        # 调用 LLM
        response = await litellm_service.chat_completion(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_instruction=system_instruction_content,
            prompt=prompt_content,
        )

        assistant_content = litellm_service.extract_message_content(response)

        # 保存助手消息
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            metadata=litellm_service.extract_usage(response),
            system_instruction_id=request.system_instruction_id,
            prompt_id=request.prompt_id,
        )
        self.db.add(assistant_message)

        await self.db.commit()

        # 构建响应
        return ChatResponse(
            session_id=session_id,
            message=ChatMessageResponse.model_validate(assistant_message),
            system_instruction=system_instruction_content,
            prompt=prompt_content,
        )

    async def get_session(self, session_id: str) -> Optional[ChatSessionResponse]:
        """获取会话信息"""
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            return ChatSessionResponse.model_validate(session)
        return None

    async def get_session_messages(self, session_id: str) -> List[ChatMessageResponse]:
        """获取会话的所有消息"""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        messages = result.scalars().all()
        return [ChatMessageResponse.model_validate(m) for m in messages]

    async def list_sessions(self, user_id: str, limit: int = 50) -> List[ChatSessionResponse]:
        """列出用户的所有会话"""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()
        return [ChatSessionResponse.model_validate(s) for s in sessions]
