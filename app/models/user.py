"""
用户模型
存储用户账户信息
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from app.db.session import Base

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """用户表 - 存储用户账户信息"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="加密后的密码")

    # 用户信息
    full_name = Column(String(100), nullable=True, comment="全名")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")

    # 账户状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否为超级管理员")
    is_verified = Column(Boolean, default=False, comment="邮箱是否验证")

    # 最后登录信息
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(50), nullable=True, comment="最后登录IP")

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    # sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str) -> None:
        """设置密码（加密存储）"""
        self.hashed_password = pwd_context.hash(password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        """类方法：生成密码哈希"""
        return pwd_context.hash(password)
