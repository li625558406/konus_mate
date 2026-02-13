"""
对话记忆相关 API 路由
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, get_current_user
from app.models.conversation_memory import ConversationMemory
from app.schemas.chat import ChatMessageContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["对话记忆"])


class MemoryResponse(BaseModel):
    """记忆响应 Schema"""
    id: int
    summary: str
    key_points: Optional[str] = None
    memory_type: str
    importance_score: int
    created_at: str

    class Config:
        from_attributes = True


class ConversationHistoryResponse(BaseModel):
    """对话历史响应 Schema"""
    messages: List[ChatMessageContext]
    total_count: int


@router.get("/list", response_model=List[MemoryResponse], summary="获取用户记忆列表")
async def get_memories(
    user_id: int = Depends(get_current_user),
    system_instruction_id: Optional[int] = Query(None, description="系统提示词ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户的记忆列表

    - **system_instruction_id**: 可选，筛选特定系统提示词的记忆
    - 返回未软删除的记忆，按重要性排序
    """
    try:
        query = select(ConversationMemory).where(
            and_(
                ConversationMemory.user_id == user_id,
                ConversationMemory.is_deleted == False
            )
        )

        if system_instruction_id:
            query = query.where(ConversationMemory.system_instruction_id == system_instruction_id)

        query = query.order_by(ConversationMemory.importance_score.desc(), ConversationMemory.created_at.desc())

        result = await db.execute(query)
        memories = result.scalars().all()

        # 格式化响应
        response_memories = []
        for memory in memories:
            from datetime import datetime
            created_at_str = memory.created_at.isoformat() if isinstance(memory.created_at, datetime) else str(memory.created_at)

            response_memories.append(
                MemoryResponse(
                    id=memory.id,
                    summary=memory.summary,
                    key_points=memory.key_points,
                    memory_type=memory.memory_type,
                    importance_score=memory.importance_score,
                    created_at=created_at_str
                )
            )

        return response_memories

    except Exception as e:
        logger.error(f"获取记忆列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取记忆列表失败: {str(e)}"
        )


@router.delete("/{memory_id}", summary="删除指定记忆")
async def delete_memory(
    memory_id: int,
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    软删除指定的记忆

    - **memory_id**: 记忆ID
    - 只能删除自己的记忆
    """
    try:
        from datetime import datetime, timezone

        result = await db.execute(
            select(ConversationMemory).where(
                and_(
                    ConversationMemory.id == memory_id,
                    ConversationMemory.user_id == user_id
                )
            )
        )
        memory = result.scalar_one_or_none()

        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="记忆不存在或无权访问"
            )

        memory.is_deleted = True
        memory.deleted_at = datetime.now(timezone.utc)
        await db.commit()

        return {"message": "记忆已删除", "id": memory_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除记忆失败: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除记忆失败: {str(e)}"
        )


@router.post("/clear-old", summary="清理旧记忆")
async def clear_old_memories(
    user_id: int = Depends(get_current_user),
    system_instruction_id: Optional[int] = Query(None, description="系统提示词ID"),
    months: int = Query(3, ge=1, le=12, description="清理几个月前的记忆"),
    db: AsyncSession = Depends(get_db),
):
    """
    清理指定月数之前的旧记忆

    - **system_instruction_id**: 可选，只清理特定系统提示词的记忆
    - **months**: 清理几个月前的记忆（默认3个月，范围1-12）
    - 软删除旧记忆
    """
    try:
        from datetime import datetime, timezone, timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30 * months)

        query = select(ConversationMemory).where(
            and_(
                ConversationMemory.user_id == user_id,
                ConversationMemory.is_deleted == False,
                ConversationMemory.created_at < cutoff_date
            )
        )

        if system_instruction_id:
            query = query.where(ConversationMemory.system_instruction_id == system_instruction_id)

        result = await db.execute(query.order_by(ConversationMemory.created_at.asc()))
        memories = result.scalars().all()

        count = 0
        for memory in memories:
            memory.is_deleted = True
            memory.deleted_at = datetime.now(timezone.utc)
            count += 1

        await db.commit()

        logger.info(f"用户 {user_id} 清理了 {count} 条旧记忆（{months}个月前）")
        return {"message": f"已清理 {count} 条旧记忆", "count": count}

    except Exception as e:
        logger.error(f"清理旧记忆失败: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理旧记忆失败: {str(e)}"
        )
