"""
对话记忆模型
用于RAG向量存储的对话清洗数据
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey, Index, Float
from sqlalchemy.orm import relationship
from app.db.session import Base


class ConversationMemory(Base):
    """对话记忆表 - 存储清洗后的对话记忆（用于RAG检索）"""

    __tablename__ = "conversation_memories"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    system_instruction_id = Column(Integer, ForeignKey("system_instructions.id"), nullable=False, index=True, comment="系统提示词ID")

    # 记忆类型：主动记忆（AI判断重要）或 被动记忆（用户强制要求）
    memory_type = Column(String(20), nullable=False, default="active", comment="记忆类型: active(主动记忆)/passive(被动记忆)")

    # 原始对话内容和清洗后的摘要
    original_content = Column(Text, nullable=True, comment="原始对话内容片段")
    summary = Column(Text, nullable=False, comment="AI清洗后的记忆摘要")
    key_points = Column(Text, nullable=True, comment="关键点列表（JSON格式）")

    # 向量嵌入（用于RAG检索）
    embedding = Column(Text, nullable=True, comment="向量嵌入（JSON数组字符串）")

    # 元数据
    conversation_round = Column(Integer, nullable=False, comment="对话轮次（第50次、第100次等）")
    importance_score = Column(Integer, default=5, comment="重要性评分 1-10")

    # 实体信息（JSON格式）
    entities = Column(Text, nullable=True, comment="实体信息（JSON格式）：{dates: [], locations: [], people: [], events: []}")

    # ========== 新增：智能记忆管理 Metadata 字段 ==========
    # 记忆分类：fact(永久事实), preference(永久喜好), event(衰减事件), desire(衰减愿望)
    memory_category = Column(String(20), nullable=True, comment="记忆分类: fact/preference/event/desire")

    # 时间戳（Unix timestamp，用于计算时间衰减）
    created_at_timestamp = Column(Integer, nullable=True, comment="创建时间戳（Unix timestamp）")

    # 访问追踪
    last_accessed = Column(Integer, nullable=True, comment="最后访问时间戳（Unix timestamp，初始值=created_at_timestamp）")
    access_count = Column(Integer, default=1, comment="访问次数（初始值=1）")

    # 情绪权重（0.1-1.0，由情绪分析Agent注入）
    emotional_weight = Column(Float, nullable=True, comment="情绪权重（0.1-1.0，越高影响越大）")

    # 语义重要性（0.1-1.0，归一化后的importance_score）
    semantic_importance = Column(Float, nullable=True, comment="语义重要性（0.1-1.0，归一化后的importance_score/10）")

    # 软删除
    is_deleted = Column(Boolean, default=False, comment="是否软删除")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 复合索引优化查询
    __table_args__ = (
        Index('ix_user_system_created', 'user_id', 'system_instruction_id', 'created_at'),
        Index('ix_user_system_deleted', 'user_id', 'system_instruction_id', 'is_deleted'),
        Index('ix_memory_category', 'memory_category'),  # 新增：按分类查询
        Index('ix_last_accessed', 'last_accessed'),  # 新增：按访问时间排序
    )
