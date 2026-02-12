"""
LiteLLM 服务
集成智谱 AI 和其他 LLM 提供商
"""
import logging
from typing import Optional, Dict, Any, List
from litellm import acompletion, completion
from app.core.config import settings

logger = logging.getLogger(__name__)


class LiteLLMService:
    """LiteLLM 服务类 - 封装所有 LLM 调用"""

    def __init__(self):
        """初始化 LiteLLM 服务"""
        self.model = settings.LITELLM_MODEL
        self.default_temperature = settings.LITELLM_TEMPERATURE
        self.default_max_tokens = settings.LITELLM_MAX_TOKENS
        self.timeout = settings.LITELLM_TIMEOUT

        # 设置 API Key
        if settings.ZHIPU_API_KEY:
            import os
            os.environ["ZHIPUAI_API_KEY"] = settings.ZHIPU_API_KEY

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        异步聊天完成接口

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成 token 数
            system_instruction: 系统提示词
            prompt: 额外的 prompt 前缀
            **kwargs: 其他参数

        Returns:
            API 响应结果
        """
        # 构建完整的消息列表
        full_messages = []

        # 添加系统提示词
        if system_instruction:
            full_messages.append({"role": "system", "content": system_instruction})

        # 添加 prompt 前缀
        if prompt:
            full_messages.append({"role": "system", "content": prompt})

        # 添加对话消息
        full_messages.extend(messages)

        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature or self.default_temperature,
            "max_tokens": max_tokens or self.default_max_tokens,
            "timeout": self.timeout,
            **kwargs
        }

        # 启用联网功能（智谱 AI 支持）
        if self.model.startswith("zhipuai"):
            request_params["tools"] = [{"type": "web_search", "web_search": {"enable": True}}]

        try:
            logger.info(f"Sending LLM request: model={self.model}, messages_count={len(full_messages)}")
            response = await acompletion(**request_params)
            logger.info(f"LLM response received: usage={response.get('usage', {})}")
            return response
        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}", exc_info=True)
            raise

    def chat_completion_sync(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        同步聊天完成接口

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            system_instruction: 系统提示词
            prompt: 额外的 prompt 前缀
            **kwargs: 其他参数

        Returns:
            API 响应结果
        """
        full_messages = []

        if system_instruction:
            full_messages.append({"role": "system", "content": system_instruction})

        if prompt:
            full_messages.append({"role": "system", "content": prompt})

        full_messages.extend(messages)

        request_params = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature or self.default_temperature,
            "max_tokens": max_tokens or self.default_max_tokens,
            **kwargs
        }

        if self.model.startswith("zhipuai"):
            request_params["tools"] = [{"type": "web_search", "web_search": {"enable": True}}]

        try:
            logger.info(f"Sending sync LLM request: model={self.model}")
            response = completion(**request_params)
            return response
        except Exception as e:
            logger.error(f"Sync LLM request failed: {str(e)}", exc_info=True)
            raise

    def extract_message_content(self, response: Dict[str, Any]) -> str:
        """从响应中提取消息内容"""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract message content: {e}")
            return ""

    def extract_usage(self, response: Dict[str, Any]) -> Dict[str, int]:
        """从响应中提取使用量信息"""
        try:
            return response.get("usage", {})
        except Exception as e:
            logger.error(f"Failed to extract usage: {e}")
            return {}


# 全局服务实例
litellm_service = LiteLLMService()
