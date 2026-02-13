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
from app.models.user_custom_prompt import UserCustomPrompt
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.litellm_service import litellm_service
from app.services.conversation_cleaner_service import (
    ConversationCleanerService,
    clean_conversation_in_background
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

    async def _get_user_custom_prompt(
        self,
        user_id: int,
        system_instruction_id: int
    ) -> Optional[str]:
        """
        获取用户自定义 prompt（基于 user_id 和 system_instruction_id）

        Args:
            user_id: 用户ID
            system_instruction_id: 系统提示词ID

        Returns:
            用户自定义 prompt 内容，如果不存在则返回 None
        """
        try:
            result = await self.db.execute(
                select(UserCustomPrompt)
                .where(
                    and_(
                        UserCustomPrompt.user_id == user_id,
                        UserCustomPrompt.system_instruction_id == system_instruction_id,
                        UserCustomPrompt.is_active == True
                    )
                )
                .order_by(UserCustomPrompt.sort_order)
                .limit(1)
            )
            custom_prompt = result.scalar_one_or_none()
            return custom_prompt.content if custom_prompt else None
        except Exception as e:
            logger.error(f"查询用户自定义 prompt 失败: {str(e)}", exc_info=True)
            return None

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

    async def _get_recent_memories(
        self,
        user_id: int,
        system_instruction_id: int,
        limit: int = 3
    ) -> List[ConversationMemory]:
        """
        查询最新的N条记忆

        Args:
            user_id: 用户ID
            system_instruction_id: 系统提示词ID
            limit: 返回数量限制

        Returns:
            最新的N条记忆列表
        """
        try:
            result = await self.db.execute(
                select(ConversationMemory)
                .where(
                    and_(
                        ConversationMemory.user_id == user_id,
                        ConversationMemory.system_instruction_id == system_instruction_id,
                        ConversationMemory.is_deleted == False
                    )
                )
                .order_by(ConversationMemory.created_at.desc())
                .limit(limit)
            )
            memories = result.scalars().all()
            logger.info(f"查询到 {len(memories)} 条最新记忆: user_id={user_id}")
            return memories
        except Exception as e:
            logger.error(f"查询最新记忆失败: {str(e)}", exc_info=True)
            return []

    def _format_memories_for_prompt(self, memories: List[ConversationMemory]) -> str:
        """
        格式化记忆列表为prompt文本（包含时间实体信息）

        Args:
            memories: 记忆列表

        Returns:
            格式化后的文本
        """
        if not memories:
            return ""

        formatted = []
        for memory in memories:
            # 解析 entities（如果存在）
            entities_info = ""
            try:
                import json
                if memory.entities:
                    entities = json.loads(memory.entities)

                    # 按类型优先级显示实体信息
                    if "dates" in entities and entities["dates"]:
                        entities_info += "\n时间："
                        for date in entities["dates"]:
                            entities_info += f"\n  - {date}"
                    if "locations" in entities and entities["locations"]:
                        entities_info += "\n地点："
                        for loc in entities["locations"]:
                            entities_info += f"\n  - {loc}"
                    if "people" in entities and entities["people"]:
                        entities_info += "\n人物："
                        for person in entities["people"]:
                            entities_info += f"\n  - {person}"
                    if "events" in entities and entities["events"]:
                        entities_info += "\n事件："
                        for event in entities["events"]:
                            entities_info += f"\n  - {event}"
            except:
                pass

            formatted.append(
                f"记忆时间：{memory.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"摘要：{memory.summary}{entities_info}"
            )

        return "\n\n---\n\n".join(formatted)

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

        # 5. 查询最新的3条记忆
        recent_memories = await self._get_recent_memories(
            user_id=user_id,
            system_instruction_id=system_instruction_id,
            limit=3
        )

        # 6. 检索相关记忆（RAG向量相似度搜索）
        last_user_message = request.messages[-1].content if request.messages else ""
        memory_context = await self._retrieve_relevant_memories(
            user_id=user_id,
            system_instruction_id=system_instruction_id,
            query=last_user_message
        )

        # 7. 查询用户自定义 prompt（新增逻辑）
        user_custom_prompt = await self._get_user_custom_prompt(
            user_id=user_id,
            system_instruction_id=system_instruction_id
        )

        # 8. 构建消息列表
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages_to_process
        ]

        # 9. 组合 prompt 内容（优先级：用户自定义 prompt > 记忆信息）
        prompt_content = None

        # 9.1 优先添加用户自定义 prompt（新增）
        if user_custom_prompt:
            prompt_content = user_custom_prompt
            logger.info(f"[USER_CUSTOM_PROMPT] Found custom prompt for user_id={user_id}, system_instruction_id={system_instruction_id}")

        # 9.2 组合最新的3条记忆到prompt中
        if recent_memories:
            memory_text = self._format_memories_for_prompt(recent_memories)
            memory_prompt = f"""以下是用户最近的对话记忆，请在回复时参考这些信息：

{memory_text}

请根据这些记忆信息，提供更个性化、更贴合用户需求的回复。"""
            # 追加到现有 prompt 后面
            if prompt_content:
                prompt_content = prompt_content + "\n\n" + memory_prompt
            else:
                prompt_content = memory_prompt

        # 9.3 如果还有RAG检索的记忆，也追加
        if memory_context:
            rag_text = f"\n\n另外，以下是与当前问题相关的历史记忆：\n\n{memory_context}"
            prompt_content = prompt_content + rag_text if prompt_content else rag_text

        # 打印最终使用的prompt（调试用）
        logger.info(f"[PROMPT] Final used prompt:\n{prompt_content}")

        # 9. 启动后台对话清洗任务
        async def background_cleaning():
            try:
                from app.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as bg_db:
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
            except Exception as e:
                logger.error(f"后台对话清洗任务失败: {str(e)}", exc_info=True)

        asyncio.create_task(background_cleaning())

        # 10. 调用 LLM（prompt参数包含RAG检索的记忆）
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
