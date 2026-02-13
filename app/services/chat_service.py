"""
聊天服务
处理聊天逻辑（支持对话次数管理、RAG检索、记忆清洗）
"""
import logging
import asyncio
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_instruction import SystemInstruction
from app.models.conversation_memory import ConversationMemory
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.litellm_service import litellm_service
from app.services.conversation_cleaner_service import (
    ConversationCleanerService,
    clean_conversation_in_background,
    soft_delete_old_memories_in_background
)

logger = logging.getLogger(__name__)


# 常量配置
# CONVERSATION_BATCH_SIZE = 50  # 每50次对话触发清洗
CONVERSATION_BATCH_SIZE = 6  # 每50次对话触发清洗

class ChatService:
    """聊天服务类 - 处理聊天业务逻辑（支持记忆管理）"""

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

    async def _retrieve_relevant_memories(
        self,
        user_id: int,
        system_instruction_id: int,
        query: str
    ) -> str:
        """检索相关记忆并格式化为文本（使用向量相似度搜索）"""
        try:
            cleaner_service = ConversationCleanerService(self.db)
            memories = await cleaner_service.get_relevant_memories(
                user_id=user_id,
                system_instruction_id=system_instruction_id,
                query=query,
                limit=5
            )

            if not memories:
                return ""

            # 格式化记忆为文本
            memory_texts = []
            for memory in memories:
                key_points = []
                try:
                    import json
                    key_points = json.loads(memory.key_points) if memory.key_points else []
                except:
                    pass

                points_str = "\n  - ".join(key_points) if key_points else "无"
                memory_texts.append(
                    f"记忆摘要: {memory.summary}\n"
                    f"关键点:\n  - {points_str}"
                )

            return "\n\n---\n\n".join(memory_texts)

        except Exception as e:
            logger.error(f"检索相关记忆失败: {str(e)}", exc_info=True)
            return ""

    async def chat(self, request: ChatRequest, user_id: int) -> ChatResponse:
        """
        处理聊天请求（支持记忆管理和对话轮转）

        Args:
            request: 聊天请求，包含 messages 列表（对话上下文）
            user_id: 当前用户ID

        Returns:
            聊天响应
        """
        # 1. 从 messages 数组长度判断对话次数
        total_messages = len(request.messages)
        logger.info(f"total_messages: total_messages==================={total_messages}")
        # 只有对话条数等于CONVERSATION_BATCH_SIZE时才触发清洗
        should_clean = total_messages >= CONVERSATION_BATCH_SIZE

        # 添加详细日志
        logger.info(f"[CHAT] user_id={user_id}, total_messages={total_messages}, CONVERSATION_BATCH_SIZE={CONVERSATION_BATCH_SIZE}, should_clean={should_clean}")

        # 2. 获取系统提示词ID
        system_instruction_id = request.system_instruction_id
        if not system_instruction_id:
            result = await self.db.execute(
                select(SystemInstruction)
                .where(SystemInstruction.is_default == True)
                .order_by(SystemInstruction.sort_order)
                .limit(1)
            )
            instruction = result.scalar_one_or_none()
            system_instruction_id = instruction.id if instruction else 1

        # 3. 不再裁剪消息，由前端控制发送的消息数量
        messages_to_process = request.messages.copy()
        conversation_round = 0

        # 计算清洗轮次
        if should_clean:
            conversation_round = (total_messages // CONVERSATION_BATCH_SIZE) * CONVERSATION_BATCH_SIZE
            logger.info(f"触发对话清洗: user_id={user_id}, round={conversation_round}, total_messages={total_messages}")

        # 4. 获取系统提示词（优先级：直接传入 > 指定ID > 默认值）
        system_instruction_content = None
        if request.system_instruction:
            system_instruction_content = request.system_instruction
        elif request.system_instruction_id:
            system_instruction_content = await self._get_system_instruction_by_id(request.system_instruction_id)
        else:
            system_instruction_content = await self._get_default_system_instruction()

        # 5. 检索相关记忆（RAG向量相似度搜索）
        last_user_message = request.messages[-1].content if request.messages else ""
        memory_context = await self._retrieve_relevant_memories(
            user_id=user_id,
            system_instruction_id=system_instruction_id,
            query=last_user_message
        )

        # 6. 构建消息列表
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages_to_process
        ]

        # 7. 如果有记忆，追加到prompt中（不是system_instruction）
        prompt_content = None
        if memory_context:
            prompt_content = f"""以下是用户的重要历史记忆，请在回复时参考这些信息：

{memory_context}

请根据这些记忆信息，提供更个性化、更贴合用户需求的回复。"""

        # 8. 启动后台任务
        # - 如果触发清洗，启动清洗任务
        # - 每次都启动软删除旧记忆任务
        async def background_tasks():
            try:
                from app.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as bg_db:
                    logger.info(f"[BACKGROUND] Starting tasks: should_clean={should_clean}")
                    if should_clean:
                        logger.info(f"[BACKGROUND] Launching cleaning task...")
                        await clean_conversation_in_background(
                            db=bg_db,
                            user_id=user_id,
                            system_instruction_id=system_instruction_id,
                            messages=[{"role": m.role, "content": m.content} for m in request.messages],
                            conversation_round=conversation_round
                        )
                    else:
                        logger.info(f"[BACKGROUND] Skipping cleaning (should_clean=False)")

                    # 每次都触发软删除检查
                    await soft_delete_old_memories_in_background(
                        db=bg_db,
                        user_id=user_id,
                        system_instruction_id=system_instruction_id
                    )
                    logger.info(f"[BACKGROUND] All tasks completed")
            except Exception as e:
                logger.error(f"后台任务执行失败: {str(e)}", exc_info=True)

        asyncio.create_task(background_tasks())

        # 8. 调用 LLM（prompt参数包含RAG检索的记忆）
        response = await litellm_service.chat_completion(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_instruction=system_instruction_content,
            prompt=prompt_content,
        )

        # 10. 提取回复内容和使用情况
        assistant_content = litellm_service.extract_message_content(response)
        usage_info = litellm_service.extract_usage(response)

        # 11. 构建响应
        return ChatResponse(
            message=assistant_content,
            usage=usage_info,
        )
