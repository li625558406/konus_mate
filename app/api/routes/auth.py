"""
认证相关 API 路由
处理用户注册、登录等
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.schemas.auth import (
    UserRegister,
    UserResponse,
    UserLogin,
    LoginResponse,
)
from app.services.auth_service import AuthService
from app.api.dependencies import get_auth_service, get_client_ip, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="用户注册")
async def register(
    data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    注册新用户

    - **username**: 用户名（3-50字符，只能包含字母、数字、下划线和连字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少6位，必须包含大小写字母和数字）
    - **full_name**: 全名（可选）
    - **phone**: 手机号（可选）
    """
    try:
        user = await auth_service.register(data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
    client_ip: str = Depends(get_client_ip),
):
    """
    用户登录

    - **username**: 用户名或邮箱
    - **password**: 密码

    返回 JWT Token 和用户信息
    """
    try:
        response = await auth_service.login(data, client_ip)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    user_id: int = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    获取当前登录用户的信息
    需要在请求头中提供 Bearer Token
    """
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


__all__ = ["router", "get_current_user"]
