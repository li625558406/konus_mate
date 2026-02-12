"""
聊天相关的 Pydantic Schema
用于请求验证和响应序列化
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class ChatMessageBase(BaseModel):
    """聊天消息基础 Schema"""

    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")


class ChatMessageCreate(ChatMessageBase):
    """创建聊天消息请求 Schema"""

    session_id: Optional[str] = Field(None, description="会话ID，首次创建时可为空")
    system_instruction_id: Optional[int] = Field(None, description="系统提示词ID")
    prompt_id: Optional[int] = Field(None, description="Prompt ID")
    metadata: Optional[dict[str, Any]] = Field(None, description="消息元数据")


class ChatMessageResponse(ChatMessageBase):
    """聊天消息响应 Schema"""

    id: int
    session_id: str
    metadata: Optional[dict[str, Any]] = Field(None, alias="message_metadata", serialization_alias="message_metadata")
    system_instruction_id: Optional[int] = None
    prompt_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class ChatSessionBase(BaseModel):
    """聊天会话基础 Schema"""

    user_id: str = Field(..., description="用户ID")
    title: Optional[str] = Field(None, description="会话标题")


class ChatSessionCreate(ChatSessionBase):
    """创建聊天会话请求 Schema"""

    system_instruction_id: Optional[int] = Field(None, description="系统提示词ID")
    prompt_id: Optional[int] = Field(None, description="Prompt ID")


class ChatSessionResponse(ChatSessionBase):
    """聊天会话响应 Schema"""

    id: str
    system_instruction_id: Optional[int] = None
    prompt_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """聊天请求 Schema"""

    message: str = Field(..., min_length=1, description="用户消息内容")
    session_id: Optional[str] = Field(None, description="会话ID，如为新会话则不提供")
    system_instruction_id: Optional[int] = Field(None, description="系统提示词ID，为空则使用默认")
    prompt_id: Optional[int] = Field(None, description="Prompt ID，为空则使用默认")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, le=32000, description="最大token数")
    stream: bool = Field(False, description="是否使用流式响应")


class ChatResponse(BaseModel):
    """聊天响应 Schema"""

    session_id: str
    message: ChatMessageResponse
    system_instruction: Optional[str] = None
    prompt: Optional[str] = None
