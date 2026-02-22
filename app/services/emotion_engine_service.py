"""
情绪引擎服务
基于 Valence-Arousal (VA) 模型的独立情绪引擎模块
"""
import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from litellm import acompletion

from app.models.character_emotion_state import CharacterEmotionState
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmotionalMath:
    """情绪数学计算类 - 纯数学逻辑，不涉及 AI"""

    # VA 空间情绪标签定义
    EMOTION_LABELS = {
        "joy": {"min_v": 0.3, "min_a": 0.3, "label": "愉悦"},
        "anger": {"max_v": -0.3, "min_a": 0.3, "label": "愤怒"},
        "sadness": {"max_v": -0.3, "max_a": -0.3, "label": "悲伤"},
        "relaxation": {"min_v": 0.3, "max_a": -0.3, "label": "放松"},
        "excited": {"min_v": 0.3, "min_a": 0.5, "label": "兴奋"},
        "anxious": {"max_v": -0.3, "min_a": 0.5, "label": "焦虑"},
        "bored": {"max_v": -0.3, "max_a": -0.5, "label": "无聊"},
        "calm": {"min_v": 0.3, "max_a": -0.5, "label": "平静"},
        "neutral": {"label": "中性"},
    }

    @staticmethod
    def clamp(value: float, min_val: float = -1.0, max_val: float = 1.0) -> float:
        """限制数值在指定范围内"""
        return max(min_val, min(max_val, value))

    @staticmethod
    def update(valence: float, arousal: float, delta_v: float, delta_a: float) -> Tuple[float, float]:
        """
        更新 VA 值，叠加增量并限制在 [-1.0, 1.0] 范围内

        Args:
            valence: 当前效价值
            arousal: 当前唤醒度
            delta_v: 效价增量
            delta_a: 唤醒度增量

        Returns:
            更新后的 (valence, arousal) 元组
        """
        new_valence = EmotionalMath.clamp(valence + delta_v)
        new_arousal = EmotionalMath.clamp(arousal + delta_a)
        return new_valence, new_arousal

    @staticmethod
    def get_state_label(valence: float, arousal: float) -> str:
        """
        根据当前 V/A 值返回情绪标签

        Args:
            valence: 效价值 [-1.0, 1.0]
            arousal: 唤醒度 [-1.0, 1.0]

        Returns:
            情绪标签字符串
        """
        # 按优先级检查情绪标签
        emotion_order = [
            "excited", "anxious", "bored", "calm",  # 更极端的情绪
            "joy", "anger", "sadness", "relaxation",  # 基础情绪
        ]

        for emotion in emotion_order:
            rule = EmotionalMath.EMOTION_LABELS[emotion]

            # 检查是否满足该情绪的条件
            if "min_v" in rule and valence < rule["min_v"]:
                continue
            if "max_v" in rule and valence > rule["max_v"]:
                continue
            if "min_a" in rule and arousal < rule["min_a"]:
                continue
            if "max_a" in rule and arousal > rule["max_a"]:
                continue

            return rule["label"]

        # 默认返回中性
        return EmotionalMath.EMOTION_LABELS["neutral"]["label"]


class JudgeService:
    """情绪分析裁判 Agent - 调用 DeepSeek 分析情绪影响"""

    # System Prompt
    SYSTEM_PROMPT = """你是一个专业的情绪分析专家。你的任务是分析用户的话语对角色情绪状态的影响。

基于 Valence-Arousal (VA) 模型：
- Valence (效价): -1.0 表示极度负面，1.0 表示极度正面
- Arousal (唤醒度): -1.0 表示极度平静，1.0 表示极度激动

你需要分析对话内容，输出该话语对角色情绪的影响增量（Delta Valence 和 Delta Arousal）。

分析规则：
1. 表扬、赞美、感谢 -> 正向 Valence 增量
2. 批评、侮辱、抱怨 -> 负向 Valence 增量
3. 激动、愤怒、惊讶 -> 正向 Arousal 增量
4. 平静、冷漠、无聊 -> 负向 Arousal 增量

增量范围通常在 -0.3 到 0.3 之间，极端情况可达到 -0.5 到 0.5。

请严格按照 JSON 格式输出，不要包含其他内容。"""

    USER_PROMPT_TEMPLATE = """当前角色情绪状态：
- Valence (效价): {current_valence:.2f}
- Arousal (唤醒度): {current_arousal:.2f}

对话历史：
{messages}

请分析最新的用户输入对角色情绪的影响，输出增量值。"""

    def __init__(self, model: str = "deepseek/deepseek-chat"):
        """
        初始化裁判服务

        Args:
            model: 使用的模型名称
        """
        self.model = model
        self.timeout = settings.LITELLM_TIMEOUT

        # 设置 DeepSeek API Key 环境变量
        if settings.DEEPSEEK_API_KEY:
            import os
            os.environ["DEEPSEEK_API_KEY"] = settings.DEEPSEEK_API_KEY

    async def analyze(
        self,
        messages: list,
        current_valence: float = 0.0,
        current_arousal: float = 0.0,
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        分析对话的情绪影响

        Args:
            messages: 对话消息列表
            current_valence: 当前效价值
            current_arousal: 当前唤醒度
            max_retries: 最大重试次数

        Returns:
            包含 delta_valence, delta_arousal, reasoning 的字典，失败返回 None
        """
        # 构建对话历史字符串
        messages_str = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages[-6:]  # 只取最近6条消息
        ])

        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            current_valence=current_valence,
            current_arousal=current_arousal,
            messages=messages_str
        )

        request_messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        for attempt in range(max_retries):
            try:
                logger.info(f"Emotion analysis attempt {attempt + 1}/{max_retries}")

                response = await acompletion(
                    model=self.model,
                    messages=request_messages,
                    temperature=0.3,  # 较低温度保证稳定性
                    max_tokens=200,
                    timeout=self.timeout
                )

                content = response["choices"][0]["message"]["content"].strip()

                # 尝试解析 JSON
                # 移除可能的 markdown 代码块标记
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                result = json.loads(content)

                # 验证必需字段
                if "delta_valence" not in result or "delta_arousal" not in result:
                    raise ValueError("Missing required fields in response")

                # 确保是数值类型
                result["delta_valence"] = float(result["delta_valence"])
                result["delta_arousal"] = float(result["delta_arousal"])

                logger.info(f"Emotion analysis success: delta_v={result['delta_valence']:.3f}, "
                          f"delta_a={result['delta_arousal']:.3f}")

                return result

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response (attempt {attempt + 1}): {e}")
                logger.debug(f"Response content: {content}")
            except (KeyError, ValueError, IndexError) as e:
                logger.warning(f"Invalid response format (attempt {attempt + 1}): {e}")
            except Exception as e:
                logger.error(f"Emotion analysis error (attempt {attempt + 1}): {e}", exc_info=True)

        logger.error(f"Emotion analysis failed after {max_retries} attempts")
        return None


class EmotionEngineService:
    """情绪引擎主服务 - 对外暴露的主接口"""

    def __init__(self, db: AsyncSession):
        """
        初始化情绪引擎服务

        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.math = EmotionalMath()
        self.judge = JudgeService()

    async def _get_or_create_emotion_state(
        self,
        user_id: int,
        char_id: int
    ) -> CharacterEmotionState:
        """
        获取或创建情绪状态记录

        Args:
            user_id: 用户ID
            char_id: 角色/系统指令ID

        Returns:
            CharacterEmotionState 实例
        """
        result = await self.db.execute(
            select(CharacterEmotionState)
            .where(CharacterEmotionState.user_id == user_id)
            .where(CharacterEmotionState.char_id == char_id)
        )

        emotion_state = result.scalar_one_or_none()

        if not emotion_state:
            # 创建新的情绪状态记录
            emotion_state = CharacterEmotionState(
                user_id=user_id,
                char_id=char_id,
                valence=0.0,
                arousal=0.0
            )
            self.db.add(emotion_state)
            await self.db.flush()
            logger.info(f"Created new emotion state for user_id={user_id}, char_id={char_id}")

        return emotion_state

    async def process_conversation(
        self,
        messages: list,
        user_id: int,
        system_instruction_id: int
    ) -> Dict[str, Any]:
        """
        处理对话，更新情绪状态（主入口方法）

        Args:
            messages: 对话消息列表
            user_id: 用户ID
            system_instruction_id: 系统/角色ID

        Returns:
            包含情绪状态和分析结果的字典
        """
        try:
            # 1. 获取当前情绪状态
            emotion_state = await self._get_or_create_emotion_state(
                user_id=user_id,
                char_id=system_instruction_id
            )

            current_valence = emotion_state.valence
            current_arousal = emotion_state.arousal

            # 2. 调用裁判 Agent 分析情绪影响
            analysis_result = await self.judge.analyze(
                messages=messages,
                current_valence=current_valence,
                current_arousal=current_arousal
            )

            # 3. 如果分析失败，使用默认值（无变化）
            if not analysis_result:
                logger.warning("Emotion analysis failed, using default values (no change)")
                delta_v = 0.0
                delta_a = 0.0
                reasoning = "分析失败，保持原状态"
            else:
                delta_v = analysis_result["delta_valence"]
                delta_a = analysis_result["delta_arousal"]
                reasoning = analysis_result.get("reasoning", "")

            # 4. 更新情绪状态
            new_valence, new_arousal = self.math.update(
                valence=current_valence,
                arousal=current_arousal,
                delta_v=delta_v,
                delta_a=delta_a
            )

            emotion_state.valence = new_valence
            emotion_state.arousal = new_arousal

            await self.db.commit()
            await self.db.refresh(emotion_state)

            # 5. 获取情绪标签
            emotion_label = self.math.get_state_label(new_valence, new_arousal)

            result = {
                "user_id": user_id,
                "char_id": system_instruction_id,
                "previous_state": {
                    "valence": round(current_valence, 3),
                    "arousal": round(current_arousal, 3),
                    "label": self.math.get_state_label(current_valence, current_arousal)
                },
                "delta": {
                    "valence": round(delta_v, 3),
                    "arousal": round(delta_a, 3)
                },
                "current_state": {
                    "valence": round(new_valence, 3),
                    "arousal": round(new_arousal, 3),
                    "label": emotion_label
                },
                "reasoning": reasoning,
                "updated_at": emotion_state.updated_at.isoformat() if emotion_state.updated_at else None
            }

            logger.info(f"Emotion state updated: user_id={user_id}, char_id={system_instruction_id}, "
                       f"V={new_valence:.2f}, A={new_arousal:.2f}, label={emotion_label}")

            return result

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error processing emotion engine: {e}", exc_info=True)
            raise

    async def get_emotion_state(
        self,
        user_id: int,
        char_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取当前情绪状态（不更新）

        Args:
            user_id: 用户ID
            char_id: 角色/系统指令ID

        Returns:
            情绪状态字典，不存在返回 None
        """
        try:
            result = await self.db.execute(
                select(CharacterEmotionState)
                .where(CharacterEmotionState.user_id == user_id)
                .where(CharacterEmotionState.char_id == char_id)
            )

            emotion_state = result.scalar_one_or_none()

            if not emotion_state:
                return None

            emotion_label = self.math.get_state_label(
                emotion_state.valence,
                emotion_state.arousal
            )

            return {
                "user_id": user_id,
                "char_id": char_id,
                "valence": round(emotion_state.valence, 3),
                "arousal": round(emotion_state.arousal, 3),
                "label": emotion_label,
                "updated_at": emotion_state.updated_at.isoformat() if emotion_state.updated_at else None,
                "created_at": emotion_state.created_at.isoformat() if emotion_state.created_at else None
            }

        except Exception as e:
            logger.error(f"Error getting emotion state: {e}", exc_info=True)
            raise

    async def reset_emotion_state(
        self,
        user_id: int,
        char_id: int
    ) -> Dict[str, Any]:
        """
        重置情绪状态到中性（0, 0）

        Args:
            user_id: 用户ID
            char_id: 角色/系统指令ID

        Returns:
            重置后的情绪状态
        """
        try:
            emotion_state = await self._get_or_create_emotion_state(
                user_id=user_id,
                char_id=char_id
            )

            emotion_state.valence = 0.0
            emotion_state.arousal = 0.0

            await self.db.commit()
            await self.db.refresh(emotion_state)

            logger.info(f"Emotion state reset: user_id={user_id}, char_id={char_id}")

            return {
                "user_id": user_id,
                "char_id": char_id,
                "valence": 0.0,
                "arousal": 0.0,
                "label": "中性",
                "updated_at": emotion_state.updated_at.isoformat() if emotion_state.updated_at else None
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error resetting emotion state: {e}", exc_info=True)
            raise
