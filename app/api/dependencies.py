"""
API 依赖注入模块
定义 FastAPI 的依赖项
"""
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.chat_service import ChatService
from app.services.system_instruction_service import SystemInstructionService
from app.services.auth_service import AuthService
from app.core.security import verify_token

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """获取聊天服务实例"""
    return ChatService(db)


async def get_system_instruction_service(db: AsyncSession = Depends(get_db)) -> SystemInstructionService:
    """获取系统提示词服务实例"""
    return SystemInstructionService(db)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> int:
    """
    获取当前登录用户 ID
    从 JWT Token 中解析用户 ID

    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户是否存在
    from app.services.auth_service import AuthService
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    return user_id


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[int]:
    """
    可选的当前用户获取
    如果未提供 Token 则返回 None，用于可选登录的接口
    """
    if credentials is None:
        return None

    token = credentials.credentials
    user_id = verify_token(token)
    return user_id


async def get_client_ip(
    x_forwarded_for: Annotated[Optional[str], Header()] = None,
    x_real_ip: Annotated[Optional[str], Header()] = None,
) -> Optional[str]:
    """
    获取客户端真实 IP 地址
    优先从 X-Forwarded-For 获取，其次 X-Real-IP
    """
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return x_real_ip
