"""
情绪分析服务
在记忆存入数据库之前，分析并注入情绪权重
"""
import json
import logging
from typing import Dict, Any, Optional
from app.services.litellm_service import litellm_service

logger = logging.getLogger(__name__)


class EmotionAnalysisService:
    """情绪分析服务 - 分析记忆的情绪强度并归一化为 0.1-1.0"""

    # 情绪分析提示词
    EMOTION_PROMPT = """你是一个专业的情感分析师。请分析以下文本的情绪强度。

**评分标准（1-10分）**：

**平淡陈述（1-3分）**：
- 客观描述事实："我吃了饭"、"今天天气不错"、"我去了XX商场"
- 简单表达喜好："我喜欢苹果"、"这个颜色还可以"
- 一般性陈述："我准备做这件事"

**中等情绪（4-6分）**：
- 带有情感的表达："我很开心"、"感觉有点累"、"这件事挺有意思"
- 明显的倾向："我真的很喜欢这个"、"我有点担心"
- 具体的感受："这个决定让我感到欣慰"

**强烈情绪（7-8分）**：
- 强烈的情感表达："我太激动了"、"我非常生气"、"我感到极度焦虑"
- 重要的人生事件："我中彩票了"、"我通过了考试"、"我被录用了"
- 深刻的感受："这让我深受触动"、"这改变了我的想法"

**极端情绪（9-10分）**：
- 极端的情绪爆发："我恨死他了"、"我简直不敢相信"、"我崩溃了"
- 人生重大转折："我结婚了"、"我孩子出生了"、"我辞职创业了"
- 深刻的生命体验："这改变了我的一生"、"我从未如此感动过"

**请分析以下文本的情绪强度，并按照以下格式返回JSON：**：

{{
  "score": 7,
  "reason": "这是一段XX性质的内容，因此评分XX"
}}

请只返回JSON，不要其他内容。

待分析文本：
{text}
"""

    @staticmethod
    async def analyze_emotion(text: str) -> Optional[float]:
        """
        分析文本的情绪强度并归一化为 0.1-1.0

        Args:
            text: 待分析文本

        Returns:
            归一化后的情绪权重（0.1-1.0），失败返回 None
        """
        try:
            # 限制文本长度，避免浪费 token
            truncated_text = text[:1000]

            # 调用 LLM 分析
            response = await litellm_service.chat_completion(
                messages=[{"role": "user", "content": EmotionAnalysisService.EMOTION_PROMPT.format(text=truncated_text)}],
                temperature=0.3,  # 使用较低的温度以获得更一致的结果
                max_tokens=500,
            )

            # 提取响应内容
            content = litellm_service.extract_message_content(response)

            # 解析 JSON
            # 尝试提取 JSON（可能被包裹在 markdown 代码块中）
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            score = result.get("score", 5)

            # 归一化：1-10 分 -> 0.1-1.0
            normalized_weight = score / 10.0

            logger.info(f"情绪分析成功: score={score}, normalized={normalized_weight:.2f}, reason={result.get('reason', 'N/A')}")
            return normalized_weight

        except json.JSONDecodeError as e:
            logger.error(f"解析情绪分析结果失败: {str(e)}, content={content[:200]}")
            return None
        except Exception as e:
            logger.error(f"情绪分析失败: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def classify_memory_type(summary: str, entities: Dict[str, Any]) -> str:
        """
        根据摘要和实体信息，分类记忆类型

        Args:
            summary: 记忆摘要
            entities: 实体信息字典

        Returns:
            记忆类型：fact/preference/event/desire
        """
        import re

        summary_lower = summary.lower()

        # 1. desire（衰减愿望）：包含"想"、"希望"、"打算"、"计划"等
        desire_keywords = ["想", "希望", "打算", "计划", "准备", "要", "想要", "愿望", "梦想"]
        if any(keyword in summary_lower for keyword in desire_keywords):
            return "desire"

        # 2. preference（永久喜好）：包含"喜欢"、"爱"、"偏爱"、"习惯"等
        preference_keywords = ["喜欢", "爱", "爱", "偏爱", "习惯", "宁愿", "倾向于", "总是"]
        if any(keyword in summary_lower for keyword in preference_keywords):
            return "preference"

        # 3. event（衰减事件）：包含时间、地点、人物、事件等实体
        if entities:
            has_temporal = bool(entities.get("dates") or entities.get("events"))
            has_spatial = bool(entities.get("locations"))
            has_people = bool(entities.get("people"))

            # 如果有时间或地点，可能是事件
            if has_temporal or has_spatial or has_people:
                # 但需要判断是永久事实还是临时事件
                fact_keywords = ["是", "叫", "住", "工作", "学习", "出生"]
                if any(keyword in summary_lower for keyword in fact_keywords):
                    return "fact"  # "我在XX公司工作" 是事实
                else:
                    return "event"  # "我去了XX商场" 是事件

        # 4. fact（永久事实）：默认分类
        return "fact"
