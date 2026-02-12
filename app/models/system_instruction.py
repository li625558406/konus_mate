"""
系统提示词模型
存储 AI 的系统级指令
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from app.db.session import Base


class SystemInstruction(Base):
    """系统提示词表 - 存储 AI 的系统级指令"""

    __tablename__ = "system_instructions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="指令名称")
    description = Column(String(500), nullable=True, comment="指令描述")
    content = Column(Text, nullable=False, comment="系统提示词内容")

    # 控制字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认指令")
    sort_order = Column(Integer, default=0, comment="排序顺序")

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
