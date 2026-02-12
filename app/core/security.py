"""
安全模块
JWT Token 生成和验证
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from app.core.config import settings

# JWT 算法
ALGORITHM = "HS256"


def create_access_token(subject: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    Args:
        subject: 用户ID
        expires_delta: 过期时间增量

    Returns:
        JWT Token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"sub": str(subject), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码并验证访问令牌

    Args:
        token: JWT Token

    Returns:
        Token 载荷，验证失败返回 None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[int]:
    """
    验证 Token 并返回用户ID

    Args:
        token: JWT Token

    Returns:
        用户ID，验证失败返回 None
    """
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id: int = int(payload.get("sub"))
    return user_id
