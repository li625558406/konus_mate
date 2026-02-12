"""
系统提示词相关的 Pydantic Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SystemInstructionBase(BaseModel):
    """系统提示词基础 Schema"""

    name: str = Field(..., min_length=1, max_length=100, description="指令名称")
    description: Optional[str] = Field(None, max_length=500, description="指令描述")
    content: str = Field(..., min_length=1, description="系统提示词内容")


class SystemInstructionCreate(SystemInstructionBase):
    """创建系统提示词请求 Schema"""

    is_active: Optional[bool] = Field(True, description="是否启用")
    is_default: Optional[bool] = Field(False, description="是否为默认指令")
    sort_order: Optional[int] = Field(0, description="排序顺序")


class SystemInstructionUpdate(BaseModel):
    """更新系统提示词请求 Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="指令名称")
    description: Optional[str] = Field(None, max_length=500, description="指令描述")
    content: Optional[str] = Field(None, min_length=1, description="系统提示词内容")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否为默认指令")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class SystemInstructionResponse(SystemInstructionBase):
    """系统提示词响应 Schema"""

    id: int
    is_active: bool
    is_default: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
