"""
角色情绪状态模型
基于 Valence-Arousal (VA) 模型持久化角色的情绪状态
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, UniqueConstraint
from app.db.session import Base


class CharacterEmotionState(Base):
    """角色情绪状态表 - 存储 VA 模型的情绪状态"""

    __tablename__ = "character_emotion_states"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    char_id = Column(Integer, nullable=False, index=True, comment="角色ID (system_instruction_id)")

    # VA 模型维度
    valence = Column(Float, nullable=False, default=0.0, comment="效价 (Valence): -1.0(负面) ~ 1.0(正面)")
    arousal = Column(Float, nullable=False, default=0.0, comment="唤醒度 (Arousal): -1.0(平静) ~ 1.0(激动)")

    # 审计字段
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 复合唯一索引：每个用户的每个角色只有一个情绪状态
    __table_args__ = (
        UniqueConstraint('user_id', 'char_id', name='uq_user_char_emotion'),
    )
