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

**特别关注时间和地点信息**：
- 如果用户提到具体时间（如"今天"、"明天"、"昨天"、"上周"、"3月15号"、"这周末"等），请在 entities.dates 中记录，格式：YYYY-MM-DD（如"2026-02-13"）
- 如果用户提到相对时间（如"过两天"、"上个月"、"上周三"等），请尽量推算具体日期并在 entities.dates 中记录
- 如果用户提到具体地点（如"去了XX商场"、"在XX公园"、"到XX餐厅"等），请在 entities.locations 中记录
- 如果用户提到人物（如"和小王"、"和李四"等），请在 entities.people 中记录
- 如果用户提到事件（如"看了电影"、"参加比赛"等），请在 entities.events 中记录

请分析以下对话内容，并按照以下格式返回JSON结果：

{{
  "summary": "这段对话的核心摘要（2-3句话）",
  "key_points": ["关键点1", "关键点2", "关键点3"],
  "importance_score": 7,
  "should_remember": true,
  "memory_type": "active",
  "reason": "为什么这段对话值得记住的原因",
  "entities": {{
    "dates": ["2026-02-13"],
    "locations": ["人民广场"],
    "people": ["小王"],
    "events": ["下午茶"]
  }}
}}

**【重要】判断标准：**

**第一类：不要保存的内容（should_remember=false）**
1. 寒暄礼貌用语：你好、在吗、在吗、你好啊、嗨、您好、谢谢、再见、拜拜、晚安等
2. 简单确认：好的、知道了、可以、没问题、行、可以可以、对、是的、没错等
3. 无意义内容：测试、测试测试、哈哈哈、呵呵、表情符号、标点符号、空内容等
4. 应答式短语：只有"是"、"不是"、"对"、"不对"、"有"、"没有"、"嗯"、"哦"等
5. 技术性回复：继续、请继续、重新生成、再试一次等
6. 单纯的疑问词：什么、怎么、如何、为什么（没有上下文）等
7. 重复内容：与已有记忆完全相同或高度相似的内容

**第二类：必须保存的内容（should_remember=true）**
1. 包含时间信息：今天、昨天、上周、去年、3月15号、周末等
2. 包含地点信息：XX商场、人民广场、XX公园、XX餐厅、公司、家、学校等
3. 包含人物信息：小王、李四、妈妈、爸爸、老板、同事、朋友等
4. 包含事件信息：看电影、吃饭、旅游、开会、运动、购物、看病等
5. 情感状态：开心、难过、焦虑、生气、疲惫、兴奋等
6. 喜好偏好：喜欢、不喜欢、爱吃、讨厌、想要、希望等
7. 重要决定：决定、计划、打算、准备做、购买了等
8. 个人信息：年龄、职业、家庭成员、工作、学习、收入等
9. 用户明确要求记住："记住这个"、"帮我记一下"、"别忘"等

**重要性评分标准（1-10分）：**
- 10分：包含时间+地点/人物+事件的完整信息
- 8-9分：包含时间+地点，或重要个人信息
- 5-7分：包含时间、地点、人物、事件中的任意一项
- 3-4分：一般性陈述，但有一定意义
- 1-2分：内容较少，但勉强有记忆价值

**memory_type标准：**
- active（主动记忆）：用户主动提到的信息（个人信息、喜好、事件等）
- passive（被动记忆）：用户明确说"记住这个"、"帮我记一下"

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

            # 3. 创建记忆记录（不保存原始对话内容，节省存储空间）
            memory = ConversationMemory(
                user_id=user_id,
                system_instruction_id=system_instruction_id,
                memory_type=cleaning_result.get("memory_type", "active"),
                original_content=None,  # 不保存原始对话内容，节省存储空间
                summary=cleaning_result["summary"],
                key_points=json.dumps(cleaning_result.get("key_points", []), ensure_ascii=False),
                conversation_round=conversation_round,
                importance_score=cleaning_result.get("importance_score", 5),
            )

            # 如果有 entities 信息，保存为 JSON
            if "entities" in cleaning_result:
                memory.entities = json.dumps(cleaning_result["entities"], ensure_ascii=False)

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

    def _extract_keywords_from_query(self, query: str) -> dict:
        """
        从用户查询中提取关键词和时间范围

        Args:
            query: 用户查询文本

        Returns:
            包含关键词和时间范围的字典
        """
        import re
        query_lower = query.lower()

        # 提取时间范围
        time_ranges = {
            "今天": 0,
            "昨天": 1,
            "前天": 2,
            "本周": 7,
            "上周": 14,
            "本月": 30,
            "上月": 60,
            "今年": 365,
            "去年": 730,
            "前年": 1095,
        }

        detected_time_range = None
        for keyword, days in time_ranges.items():
            if keyword in query:
                detected_time_range = days
                break

        # 提取关键词（去除常见停用词）
        stopwords = {"的", "了", "是", "我", "你", "他", "她", "它", "什么", "哪", "怎样", "如何", "吗", "呢", "啊"}
        words = re.findall(r'[\w]+', query_lower)
        keywords = [w for w in words if w not in stopwords and len(w) > 1]

        return {
            "keywords": keywords,
            "time_range_days": detected_time_range,
            "raw_query": query_lower
        }

    async def _calculate_entity_match_score(
        self,
        memory: ConversationMemory,
        query_info: dict
    ) -> float:
        """
        计算记忆的entities与查询的匹配分数

        Args:
            memory: 记忆对象
            query_info: 查询信息（包含keywords和time_range_days）

        Returns:
            entities匹配分数 (0.0 - 1.0+)
        """
        if not memory.entities:
            return 0.0

        try:
            import json
            from datetime import timedelta

            entities = json.loads(memory.entities)
            score = 0.0
            query_lower = query_info["raw_query"]
            keywords = query_info["keywords"]

            # 1. 地点匹配 (权重最高: 0.4)
            if "locations" in entities and entities["locations"]:
                for loc in entities["locations"]:
                    loc_lower = loc.lower()
                    # 完全匹配
                    if loc_lower in query_lower or query_lower in loc_lower:
                        score += 0.4
                        logger.debug(f"地点匹配: {loc} -> +0.4")
                    # 关键词匹配
                    elif any(kw in loc_lower or loc_lower in kw for kw in keywords):
                        score += 0.2
                        logger.debug(f"地点部分匹配: {loc} -> +0.2")

            # 2. 时间范围匹配 (权重: 0.3)
            if "dates" in entities and entities["dates"] and query_info["time_range_days"]:
                try:
                    from datetime import datetime
                    cutoff_date = datetime.utcnow() - timedelta(days=query_info["time_range_days"] + 30)  # +30天容差

                    for date_str in entities["dates"]:
                        try:
                            memory_date = datetime.fromisoformat(date_str)
                            if memory_date >= cutoff_date:
                                score += 0.3
                                logger.debug(f"时间范围匹配: {date_str} -> +0.3")
                                break
                        except:
                            pass
                except Exception as e:
                    logger.debug(f"时间解析失败: {e}")

            # 3. 人物匹配 (权重: 0.2)
            if "people" in entities and entities["people"]:
                for person in entities["people"]:
                    person_lower = person.lower()
                    if person_lower in query_lower or query_lower in person_lower:
                        score += 0.2
                        logger.debug(f"人物匹配: {person} -> +0.2")
                    elif any(kw in person_lower or person_lower in kw for kw in keywords):
                        score += 0.1

            # 4. 事件匹配 (权重: 0.1)
            if "events" in entities and entities["events"]:
                for event in entities["events"]:
                    event_lower = event.lower()
                    if event_lower in query_lower or query_lower in event_lower:
                        score += 0.1
                        logger.debug(f"事件匹配: {event} -> +0.1")
                    elif any(kw in event_lower or event_lower in kw for kw in keywords):
                        score += 0.05

            return min(score, 1.0)  # 最高1.0分

        except Exception as e:
            logger.debug(f"计算entities匹配分数失败: {e}")
            return 0.0

    async def get_relevant_memories(
        self,
        user_id: int,
        system_instruction_id: int,
        query: str,
        limit: int = 5
    ) -> List[ConversationMemory]:
        """
        检索相关记忆（混合检索：向量相似度 + entities匹配）

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

            # 2. 提取查询信息
            query_info = self._extract_keywords_from_query(query)
            logger.info(f"查询分析: keywords={query_info['keywords']}, time_range={query_info['time_range_days']}")

            # 3. 计算混合相似度
            memories_with_scores = []
            for memory in memories:
                # 向量相似度 (50%权重)
                vector_score = await self._calculate_similarity(query, memory.summary)

                # entities匹配分数 (30%权重)
                entity_score = await self._calculate_entity_match_score(memory, query_info)

                # 重要性评分 (20%权重)
                importance_score = memory.importance_score / 10

                # 综合评分
                combined_score = (
                    vector_score * 0.5 +
                    entity_score * 0.3 +
                    importance_score * 0.2
                )

                memories_with_scores.append((memory, combined_score, {
                    "vector": vector_score,
                    "entity": entity_score,
                    "importance": importance_score
                }))

            # 4. 按综合评分排序并返回top N
            memories_with_scores.sort(key=lambda x: x[1], reverse=True)
            top_memories = [m[0] for m in memories_with_scores[:limit]]

            # 记录评分详情（调试用）
            if memories_with_scores:
                top_scores = memories_with_scores[:limit]
                logger.info(f"混合检索: query='{query[:50]}...', 找到{len(top_memories)}条相关记忆")
                for i, (mem, score, details) in enumerate(top_scores, 1):
                    logger.debug(f"  TOP{i}: score={score:.3f} (v={details['vector']:.3f}, e={details['entity']:.3f}, i={details['importance']:.3f}) - {mem.summary[:30]}")

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
