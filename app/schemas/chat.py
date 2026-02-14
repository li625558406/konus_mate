"""
聊天相关的 Pydantic Schema
用于请求验证和响应序列化
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field, model_validator
from pydantic import ValidationError


class ChatMessageContext(BaseModel):
    """聊天消息上下文 Schema"""

    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求 Schema"""

    # 对话上下文列表（多轮对话历史）
    messages: List[ChatMessageContext] = Field(
        ...,
        description="对话上下文列表，包含多轮对话历史",
        min_length=1  # 至少包含一条消息
    )

    # 可选的系统提示词和 prompt（用户可以直接传入，也可以通过 ID 指定）
    system_instruction: Optional[str] = Field(None, description="系统提示词内容，直接传入")
    system_instruction_id: Optional[int] = Field(None, description="系统提示词ID，为空则使用默认")
    prompt: Optional[str] = Field(None, description="Prompt 内容，直接传入")
    prompt_id: Optional[int] = Field(None, description="Prompt ID，为空则使用默认")

    # LLM 参数
    temperature: Optional[float] = Field(None, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, le=32000, description="最大token数")
    stream: bool = Field(False, description="是否使用流式响应")

    @model_validator(mode='after')
    def validate_messages(self):
        """验证消息数组不为空且内容有效"""
        if not self.messages:
            raise ValueError("messages 数组不能为空")

        # 验证每条消息的 content 不为空
        for i, msg in enumerate(self.messages):
            if not msg.content or not msg.content.strip():
                raise ValueError(f"第 {i+1} 条消息的 content 不能为空")
            # 验证 role 值合法
            if msg.role not in ["user", "assistant", "system"]:
                raise ValueError(f"第 {i+1} 条消息的 role 必须是 'user'、'assistant' 或 'system'")

        return self


class ChatResponse(BaseModel):
    """聊天响应 Schema"""

    message: str = Field(..., description="AI 回复内容")
    usage: Optional[dict[str, Any]] = Field(None, description="Token 使用情况")
