"""
Prompt 模型
存储对话提示词模板
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from app.db.session import Base


class Prompt(Base):
    """Prompt 表 - 存储对话提示词模板"""

    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="Prompt 名称")
    description = Column(String(500), nullable=True, comment="Prompt 描述")
    content = Column(Text, nullable=False, comment="Prompt 内容")

    # Prompt 分类
    category = Column(String(50), nullable=True, comment="Prompt 分类")
    tags = Column(String(500), nullable=True, comment="标签，逗号分隔")

    # 控制字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认 prompt")
    sort_order = Column(Integer, default=0, comment="排序顺序")

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
