"""
认证相关的 Pydantic Schema
用于登录、注册等认证操作
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """用户基础 Schema"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")


class UserRegister(UserBase):
    """用户注册请求 Schema"""

    password: str = Field(..., min_length=6, max_length=50, description="密码")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class UserLogin(BaseModel):
    """用户登录请求 Schema"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应 Schema"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class UserResponse(UserBase):
    """用户信息响应 Schema"""

    id: int
    avatar_url: Optional[str] = None
    is_active: bool
    is_superuser: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(TokenResponse):
    """登录响应 Schema - 包含 Token 和用户信息"""

    user: UserResponse = Field(..., description="用户信息")


class TokenPayload(BaseModel):
    """Token 载荷 Schema - 用于 JWT 解析"""

    sub: int = Field(..., description="用户ID")
    exp: Optional[int] = Field(None, description="过期时间戳")
