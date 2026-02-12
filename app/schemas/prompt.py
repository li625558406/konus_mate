"""
Prompt 相关的 Pydantic Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PromptBase(BaseModel):
    """Prompt 基础 Schema"""

    name: str = Field(..., min_length=1, max_length=100, description="Prompt 名称")
    description: Optional[str] = Field(None, max_length=500, description="Prompt 描述")
    content: str = Field(..., min_length=1, description="Prompt 内容")
    category: Optional[str] = Field(None, max_length=50, description="Prompt 分类")
    tags: Optional[str] = Field(None, max_length=500, description="标签，逗号分隔")


class PromptCreate(PromptBase):
    """创建 Prompt 请求 Schema"""

    is_active: Optional[bool] = Field(True, description="是否启用")
    is_default: Optional[bool] = Field(False, description="是否为默认 prompt")
    sort_order: Optional[int] = Field(0, description="排序顺序")


class PromptUpdate(BaseModel):
    """更新 Prompt 请求 Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Prompt 名称")
    description: Optional[str] = Field(None, max_length=500, description="Prompt 描述")
    content: Optional[str] = Field(None, min_length=1, description="Prompt 内容")
    category: Optional[str] = Field(None, max_length=50, description="Prompt 分类")
    tags: Optional[str] = Field(None, max_length=500, description="标签，逗号分隔")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否为默认 prompt")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class PromptResponse(PromptBase):
    """Prompt 响应 Schema"""

    id: int
    is_active: bool
    is_default: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
