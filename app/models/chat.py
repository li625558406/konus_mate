"""
聊天记录模型
存储用户与 AI 的对话历史
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class ChatSession(Base):
    """聊天会话表 - 表示一个完整的对话会话"""

    __tablename__ = "chat_sessions"

    id = Column(String(64), primary_key=True, comment="会话ID")
    user_id = Column(String(64), nullable=False, index=True, comment="用户ID")
    title = Column(String(255), nullable=True, comment="会话标题")
    system_instruction_id = Column(Integer, ForeignKey("system_instructions.id"), nullable=True, comment="关联的系统提示词ID")
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True, comment="关联的prompt ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """聊天消息表 - 存储单条消息"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="消息ID")
    session_id = Column(String(64), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True, comment="会话ID")
    role = Column(String(20), nullable=False, comment="角色: user/assistant/system")
    content = Column(Text, nullable=False, comment="消息内容")

    # 存储消息的元数据（如模型参数、token使用量等）
    message_metadata = Column(JSON, nullable=True, comment="消息元数据")

    # 记录使用的 system_instruction 和 prompt
    system_instruction_id = Column(Integer, ForeignKey("system_instructions.id"), nullable=True, comment="使用的系统提示词ID")
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True, comment="使用的prompt ID")

    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    session = relationship("ChatSession", back_populates="messages")
