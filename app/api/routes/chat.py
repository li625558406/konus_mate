"""
聊天相关 API 路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageResponse, ChatSessionResponse
from app.services.chat_service import ChatService
from app.api.dependencies import get_chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post("", response_model=ChatResponse, summary="发送聊天消息")
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    发送聊天消息并获取 AI 响应

    - **message**: 用户消息内容
    - **session_id**: 会话ID，新会话可不提供
    - **system_instruction_id**: 系统提示词ID，为空则使用默认
    - **prompt_id**: Prompt ID，为空则使用默认
    - **temperature**: 温度参数 (0-2)
    - **max_tokens**: 最大 token 数
    - **stream**: 是否使用流式响应（暂未实现）
    """
    try:
        response = await chat_service.chat(request)
        return response
    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天请求失败: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse, summary="获取会话信息")
async def get_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """获取指定会话的信息"""
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse], summary="获取会话消息")
async def get_session_messages(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """获取指定会话的所有消息"""
    messages = await chat_service.get_session_messages(session_id)
    return messages


@router.get("/sessions", response_model=list[ChatSessionResponse], summary="获取用户会话列表")
async def list_sessions(
    user_id: str = "default_user",
    limit: int = 50,
    chat_service: ChatService = Depends(get_chat_service),
):
    """获取用户的所有会话列表"""
    sessions = await chat_service.list_sessions(user_id, limit)
    return sessions
