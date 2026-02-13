"""
用户自定义 Prompt 模型
存储用户对不同系统提示词的自定义 prompt 前缀
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, UniqueConstraint
from app.db.session import Base


class UserCustomPrompt(Base):
    """用户自定义 Prompt 表 - 用户对不同 system_instruction 的自定义 prompt"""

    __tablename__ = "user_custom_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    system_instruction_id = Column(Integer, nullable=False, index=True, comment="系统提示词ID")

    # 自定义 prompt 内容
    name = Column(String(100), nullable=False, comment="自定义 prompt 名称")
    description = Column(String(500), nullable=True, comment="自定义 prompt 描述")
    content = Column(Text, nullable=False, comment="自定义 prompt 内容")

    # 控制字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序顺序")

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 唯一约束：一个用户对一个 system_instruction 只能有一条生效的自定义 prompt
    __table_args__ = (
        UniqueConstraint('user_id', 'system_instruction_id', name='uq_user_system_prompt'),
    )
