"""
认证服务
处理用户注册、登录等认证逻辑
"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, UserResponse, LoginResponse
from app.core.security import create_access_token, verify_token

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类 - 处理用户认证业务逻辑"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserRegister) -> UserResponse:
        """
        用户注册

        Args:
            data: 注册数据

        Returns:
            用户信息
        """
        # 检查用户名是否已存在
        result = await self.db.execute(
            select(User).where(User.username == data.username)
        )
        if result.scalar_one_or_none():
            raise ValueError("用户名已被注册")

        # 检查邮箱是否已存在
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none():
            raise ValueError("邮箱已被注册")

        # 创建新用户
        user = User(
            username=data.username,
            email=data.email,
            full_name=data.full_name,
            phone=data.phone,
        )
        user.set_password(data.password)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"New user registered: {user.username}")
        return UserResponse.model_validate(user)

    async def login(self, data: UserLogin, client_ip: Optional[str] = None) -> LoginResponse:
        """
        用户登录

        Args:
            data: 登录数据
            client_ip: 客户端 IP 地址

        Returns:
            登录响应（包含 Token 和用户信息）
        """
        # 尝试通过用户名或邮箱查找用户
        result = await self.db.execute(
            select(User).where(
                (User.username == data.username) | (User.email == data.username)
            )
        )
        user = result.scalar_one_or_none()

        # 验证用户和密码
        if not user or not user.verify_password(data.password):
            raise ValueError("用户名或密码错误")

        # 检查账户是否激活
        if not user.is_active:
            raise ValueError("账户已被禁用")

        # 更新最后登录信息
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip
        await self.db.commit()

        # 生成访问令牌
        access_token = create_access_token(subject=user.id)

        logger.info(f"User logged in: {user.username}")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=60 * 60 * 24 * 7,  # 7 天
            user=UserResponse.model_validate(user)
        )

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """
        根据 ID 获取用户

        Args:
            user_id: 用户ID

        Returns:
            用户信息
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            return UserResponse.model_validate(user)
        return None

    async def update_last_login(self, user_id: int, client_ip: Optional[str] = None) -> None:
        """
        更新用户最后登录信息

        Args:
            user_id: 用户ID
            client_ip: 客户端 IP
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = client_ip
            await self.db.commit()
