"""
记忆重排序服务
实现时间衰减、访问增强、情绪加权的智能排序算法
"""
import math
import time
import logging
from typing import List, Tuple, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class MemoryRankingService:
    """记忆重排序服务 - 混合多种因素进行智能排序"""

    @staticmethod
    def calculate_final_score(
        memory: ConversationMemory,
        vector_similarity: float,
        decay_rate_hours: int = 24
    ) -> float:
        """
        计算记忆的最终评分

        Args:
            memory: 记忆对象（包含 metadata 字段）
            vector_similarity: 向量相似度（0.0-1.0）
            decay_rate_hours: 衰减速率（默认24小时半衰期）

        Returns:
            最终评分（越高越相关）
        """
        try:
            # ========== 1. 获取基础变量 ==========
            current_time = int(time.time())
            created_at = memory.created_at_timestamp or current_time
            last_accessed = memory.last_accessed or created_at
            access_count = memory.access_count or 1
            emotional_weight = memory.emotional_weight or 0.5
            memory_category = memory.memory_category or "fact"

            # 计算时间差（小时）
            time_diff_hours = (current_time - created_at) / 3600

            # ========== 2. 计算 Time Decay（时间衰减）==========
            # fact/preference（永久记忆）不衰减
            # event/desire（衰减记忆）按指数衰减
            if memory_category in ["fact", "preference"]:
                decay_factor = 1.0  # 永久记忆不衰减
            else:
                # 这里的 24 是半衰期，意味着24小时后权重减半
                # 公式：decay = 1 / (1 + (time_diff / decay_rate))
                decay_factor = 1.0 / (1.0 + (time_diff_hours / decay_rate_hours))

            # ========== 3. 计算 Access Boost（访问增强）==========
            # log函数让增长变平缓，防止被访问1000次后权重无限大
            # math.log(x, 10) 表示以10为底的对数
            # 公式：boost = 1 + log(access_count, 10)
            boost_factor = 1.0 + math.log(access_count, 10) if access_count > 0 else 1.0

            # ========== 4. 计算 Emotional Boost（情绪加权）==========
            # 情绪越重，作为乘数的影响力越大
            # 公式：emotion = 1 + (emotion * 0.5)
            # 0.1情绪 -> 1.05倍
            # 1.0情绪 -> 1.50倍
            emotion_factor = 1.0 + (emotional_weight * 0.5)

            # ========== 5. 最终公式 ==========
            # Final Score = VectorSimilarity * TimeDecay * AccessBoost * EmotionalBoost
            final_score = (
                vector_similarity *
                decay_factor *
                boost_factor *
                emotion_factor
            )

            # 调试日志（只记录前10条）
            if logger.level <= logging.DEBUG:
                logger.debug(
                    f"Score计算: vector={vector_similarity:.3f}, "
                    f"decay={decay_factor:.3f} (category={memory_category}, "
                    f"boost={boost_factor:.3f} (access={access_count}), "
                    f"emotion={emotion_factor:.3f} (weight={emotional_weight:.2f}) "
                    f"-> final={final_score:.3f}"
                )

            return final_score

        except Exception as e:
            logger.error(f"计算最终评分失败: {str(e)}")
            # 出错时返回基础向量相似度
            return vector_similarity

    async def rerank_memories(
        self,
        db: AsyncSession,
        user_id: int,
        system_instruction_id: int,
        query: str,
        limit: int = 5,
        candidates_limit: int = 50
    ) -> List[ConversationMemory]:
        """
        混合检索并重排序（Oversampling + Reranking）

        Args:
            db: 数据库会话
            user_id: 用户ID
            system_instruction_id: 系统提示词ID
            query: 查询文本
            limit: 最终返回数量（默认5）
            candidates_limit: 候选集大小（默认50）

        Returns:
            重排序后的Top-N记忆列表
        """
        try:
            # ========== 1. 过采样（Oversampling）==========
            # 查询 candidates_limit 条候选记忆，而非直接取 limit 条
            result = await db.execute(
                select(ConversationMemory)
                .where(
                    and_(
                        ConversationMemory.user_id == user_id,
                        ConversationMemory.system_instruction_id == system_instruction_id,
                        ConversationMemory.is_deleted == False
                    )
                )
                .order_by(ConversationMemory.importance_score.desc())
                .limit(candidates_limit)  # 获取更大的候选集
            )
            memories = result.scalars().all()

            if not memories:
                logger.info("没有找到候选记忆")
                return []

            logger.info(f"过采样：从 {len(memories)} 条候选记忆中重排序")

            # ========== 2. 计算向量相似度（假设已有）==========
            # 注意：这里简化处理，实际应该调用向量相似度计算
            # 如果没有向量相似度，可以全部设为0.5（中性）
            # 或根据其他因素估算
            memories_with_scores = []

            for memory in memories:
                # 简化：如果有embedding字段，计算真实向量相似度
                # 这里使用简化方案：基于语义重要性
                vector_similarity = memory.semantic_importance or 0.5

                # 调用重排序算法
                final_score = self.calculate_final_score(
                    memory=memory,
                    vector_similarity=vector_similarity,
                    decay_rate_hours=24  # 24小时半衰期
                )

                memories_with_scores.append((final_score, memory))

            # ========== 3. 按最终分数倒序排列 ==========
            memories_with_scores.sort(key=lambda x: x[0], reverse=True)

            # ========== 4. 返回Top-N ==========
            top_memories = [mem[1] for mem in memories_with_scores[:limit]]

            # 记录调试信息
            logger.info(f"重排序完成：返回Top-{limit}记忆")
            if logger.level <= logging.DEBUG:
                for i, (score, mem) in enumerate(memories_with_scores[:limit], 1):
                    logger.debug(
                        f"  TOP{i}: score={score:.3f} - "
                        f"[category={mem.memory_category}, "
                        f"access={mem.access_count}, "
                        f"emotion={mem.emotional_weight:.2f}] "
                        f"{mem.summary[:30]}"
                    )

            return top_memories

        except Exception as e:
            logger.error(f"重排序失败: {str(e)}", exc_info=True)
            return []
