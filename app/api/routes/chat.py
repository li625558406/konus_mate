"""
聊天相关 API 路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.api.dependencies import get_chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post("", response_model=ChatResponse, summary="发送聊天消息（支持上下文）")
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    发送聊天消息并获取 AI 响应（支持多轮对话上下文）

    - **messages**: 对话上下文列表，包含多轮对话历史（必填）
      - 每个消息包含 role (user/assistant/system) 和 content
    - **system_instruction**: 系统提示词内容（可选，直接传入）
    - **system_instruction_id**: 系统提示词ID（可选，从数据库获取）
    - **temperature**: 温度参数 (0-2)
    - **max_tokens**: 最大 token 数
    - **stream**: 是否使用流式响应（暂未实现）

    优先级规则：
    - system_instruction > system_instruction_id > 默认值
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
