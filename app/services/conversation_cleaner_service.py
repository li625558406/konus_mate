"""
对话清洗服务
使用AI清洗对话内容，保留关键记忆
"""
import json
import logging
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.litellm_service import litellm_service
from app.models.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class ConversationCleanerService:
    """对话清洗服务 - 使用AI清洗并存储关键记忆"""

    # 清洗提示词模板
    CLEANING_PROMPT = """你是一个专业的对话记忆分析师。请分析以下对话内容，提取出需要长期记忆的重要信息。

对话背景：这是一个AI伴侣的对话记录。

请分析以下对话内容，并按照以下格式返回JSON结果：

{{
  "summary": "这段对话的核心摘要（2-3句话）",
  "key_points": ["关键点1", "关键点2", "关键点3"],
  "importance_score": 7,
  "should_remember": true,
  "memory_type": "active",
  "reason": "为什么这段对话值得记住的原因"
}}

判断标准：
1. **主动记忆（active）**：用户主动提到的个人信息、喜好、重要事件、情感状态等
2. **被动记忆（passive）**：用户明确要求AI记住的信息
3. **重要性评分**：1-10分，10分为最重要
4. **should_remember**：只有true的记忆才会被保存

对话内容：
{conversation_text}

请只返回JSON，不要其他内容。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._embedding_model = None

    async def _get_embedding_model(self):
        """延迟加载向量嵌入模型"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # 使用轻量级中文模型
                model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                self._embedding_model = SentenceTransformer(model_name)
                logger.info(f"成功加载向量嵌入模型: {model_name}")
            except ImportError:
                logger.warning("sentence-transformers未安装，将使用简化的相似度计算")
                self._embedding_model = "fallback"
            except Exception as e:
                logger.error(f"加载向量嵌入模型失败: {str(e)}")
                self._embedding_model = "fallback"
        return self._embedding_model

    async def _encode_text(self, text: str) -> Optional[np.ndarray]:
        """将文本编码为向量"""
        try:
            model = await self._get_embedding_model()
            if model == "fallback":
                return None

            # sentence-transformers 是同步的，需要在事件循环中运行
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, model.encode, text
            )
            return embedding
        except Exception as e:
            logger.error(f"文本向量化失败: {str(e)}")
            return None

    async def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度"""
        try:
            emb1 = await self._encode_text(text1)
            emb2 = await self._encode_text(text2)

            if emb1 is None or emb2 is None:
                # 回退到简单的关键词匹配
                words1 = set(text1.lower().split())
                words2 = set(text2.lower().split())
                if not words1 or not words2:
                    return 0.0
                intersection = words1.intersection(words2)
                return len(intersection) / min(len(words1), len(words2))

            # 余弦相似度
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            return float(similarity)
        except Exception as e:
            logger.error(f"计算相似度失败: {str(e)}")
            return 0.0

    async def clean_and_store_conversation(
        self,
        user_id: int,
        system_instruction_id: int,
        messages: List[Dict[str, str]],
        conversation_round: int
    ) -> List[ConversationMemory]:
        """
        清洗对话并存储到向量数据库

        Args:
            user_id: 用户ID
            system_instruction_id: 系统提示词ID
            messages: 对话消息列表
            conversation_round: 对话轮次（50, 100, 150...）

        Returns:
            保存的记忆列表
        """
        try:
            # 1. 将对话转换为文本
            conversation_text = self._format_conversation(messages)

            # 2. 使用AI清洗对话
            cleaning_result = await self._ai_clean_conversation(conversation_text)

            if not cleaning_result or not cleaning_result.get("should_remember"):
                logger.info(f"对话轮次 {conversation_round} 的内容不需要保存")
                return []

            # 3. 创建记忆记录（包含向量嵌入）
            memory = ConversationMemory(
                user_id=user_id,
                system_instruction_id=system_instruction_id,
                memory_type=cleaning_result.get("memory_type", "active"),
                original_content=conversation_text[:5000],  # 限制原始内容长度
                summary=cleaning_result["summary"],
                key_points=json.dumps(cleaning_result.get("key_points", []), ensure_ascii=False),
                conversation_round=conversation_round,
                importance_score=cleaning_result.get("importance_score", 5),
            )

            # 4. 生成向量嵌入（异步）
            summary_text = cleaning_result["summary"]
            embedding = await self._encode_text(summary_text)

            if embedding is not None:
                # 将向量转换为JSON字符串存储
                memory.embedding = json.dumps(embedding.tolist(), ensure_ascii=False)

            self.db.add(memory)
            await self.db.commit()
            await self.db.refresh(memory)

            logger.info(f"成功保存对话记忆: user_id={user_id}, round={conversation_round}, summary={memory.summary[:50]}")
            return [memory]

        except Exception as e:
            logger.error(f"清洗对话失败: {str(e)}", exc_info=True)
            await self.db.rollback()
            return []

    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """格式化对话为文本"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            role_name = {"user": "用户", "assistant": "AI助手", "system": "系统"}.get(role, role)
            formatted.append(f"{role_name}: {content}")
        return "\n\n".join(formatted)

    async def _ai_clean_conversation(self, conversation_text: str) -> Optional[Dict[str, Any]]:
        """使用AI清洗对话内容"""
        try:
            prompt = self.CLEANING_PROMPT.format(conversation_text=conversation_text[:8000])

            response = await litellm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # 使用较低的温度以获得更一致的结果
                max_tokens=1000,
            )

            content = litellm_service.extract_message_content(response)

            # 解析JSON响应
            # 尝试提取JSON（可能被包裹在markdown代码块中）
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"解析AI清洗结果失败: {str(e)}, content={content[:200]}")
            return None
        except Exception as e:
            logger.error(f"AI清洗失败: {str(e)}", exc_info=True)
            return None

    async def soft_delete_old_memories(
        self,
        user_id: int,
        system_instruction_id: int,
        months: int = 3
    ) -> int:
        """
        软删除指定月数之前的旧记忆

        Args:
            user_id: 用户ID
            system_instruction_id: 系统提示词ID
            months: 月数（默认3个月）

        Returns:
            删除的记录数
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=30 * months)

            # 查找需要软删除的记录（创建时间最老的）
            result = await self.db.execute(
                select(ConversationMemory)
                .where(
                    and_(
                        ConversationMemory.user_id == user_id,
                        ConversationMemory.system_instruction_id == system_instruction_id,
                        ConversationMemory.is_deleted == False,
                        ConversationMemory.created_at < cutoff_date
                    )
                )
                .order_by(ConversationMemory.created_at.asc())
            )
            memories_to_delete = result.scalars().all()

            count = 0
            for memory in memories_to_delete:
                memory.is_deleted = True
                memory.deleted_at = datetime.utcnow()
                count += 1

            await self.db.commit()
            logger.info(f"软删除了 {count} 条旧记忆（{months}个月前）")
            return count

        except Exception as e:
            logger.error(f"软删除旧记忆失败: {str(e)}", exc_info=True)
            await self.db.rollback()
            return 0

    async def get_relevant_memories(
        self,
        user_id: int,
        system_instruction_id: int,
        query: str,
        limit: int = 5
    ) -> List[ConversationMemory]:
        """
        检索相关记忆（使用向量相似度搜索）

        Args:
            user_id: 用户ID
            system_instruction_id: 系统提示词ID
            query: 查询文本
            limit: 返回数量限制

        Returns:
            相关记忆列表（按相似度排序）
        """
        try:
            # 1. 查找所有未删除的记忆
            result = await self.db.execute(
                select(ConversationMemory)
                .where(
                    and_(
                        ConversationMemory.user_id == user_id,
                        ConversationMemory.system_instruction_id == system_instruction_id,
                        ConversationMemory.is_deleted == False
                    )
                )
                .order_by(ConversationMemory.importance_score.desc())
                .limit(50)  # 先获取候选集
            )
            memories = result.scalars().all()

            if not memories:
                return []

            # 2. 计算相似度
            memories_with_scores = []
            for memory in memories:
                # 使用摘要计算相似度
                similarity = await self._calculate_similarity(query, memory.summary)

                # 综合考虑相似度和重要性评分
                combined_score = similarity * 0.7 + (memory.importance_score / 10) * 0.3

                memories_with_scores.append((memory, combined_score))

            # 3. 按综合评分排序并返回top N
            memories_with_scores.sort(key=lambda x: x[1], reverse=True)
            top_memories = [m[0] for m in memories_with_scores[:limit]]

            logger.info(f"向量相似度搜索: query='{query[:50]}...', 找到{len(top_memories)}条相关记忆")
            return top_memories

        except Exception as e:
            logger.error(f"检索相关记忆失败: {str(e)}", exc_info=True)
            return []


async def clean_conversation_in_background(
    db: AsyncSession,
    user_id: int,
    system_instruction_id: int,
    messages: List[Dict[str, str]],
    conversation_round: int
):
    """
    异步后台任务：清洗对话并存储
    """
    try:
        service = ConversationCleanerService(db)
        await service.clean_and_store_conversation(
            user_id=user_id,
            system_instruction_id=system_instruction_id,
            messages=messages,
            conversation_round=conversation_round
        )
    except Exception as e:
        logger.error(f"后台对话清洗任务失败: {str(e)}", exc_info=True)


async def soft_delete_old_memories_in_background(
    db: AsyncSession,
    user_id: int,
    system_instruction_id: int
):
    """
    异步后台任务：软删除旧记忆
    """
    try:
        service = ConversationCleanerService(db)
        await service.soft_delete_old_memories(
            user_id=user_id,
            system_instruction_id=system_instruction_id,
            months=3
        )
    except Exception as e:
        logger.error(f"后台删除旧记忆任务失败: {str(e)}", exc_info=True)
