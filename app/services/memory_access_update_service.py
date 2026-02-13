"""
记忆访问更新服务
在LLM生成回复后，更新被使用的记忆的访问统计
"""
import time
import logging
from typing import List
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class MemoryAccessUpdateService:
    """记忆访问更新服务 - 反馈闭环，让记忆越用越灵"""

    @staticmethod
    async def update_memory_access(
        db: AsyncSession,
        memory_ids: List[int]
    ) -> int:
        """
        更新指定记忆的访问统计

        Args:
            db: 数据库会话
            memory_ids: 被更新的记忆ID列表

        Returns:
            成功更新的记录数
        """
        if not memory_ids:
            logger.debug("没有需要更新的记忆ID")
            return 0

        try:
            current_timestamp = int(time.time())

            # 批量更新（原子操作）
            # update({
            #     last_accessed: current_timestamp,
            #     access_count: db.increment(1)
            # })
            result = await db.execute(
                update(ConversationMemory)
                .where(ConversationMemory.id.in_(memory_ids))
                .values(
                    last_accessed=current_timestamp,
                    access_count=ConversationMemory.access_count + 1
                )
                .execution_options(synchronize_session="fetch")
            )

            updated_count = result.rowcount
            await db.commit()

            logger.info(f"访问更新成功: 更新了 {updated_count} 条记忆的访问统计")
            return updated_count

        except Exception as e:
            logger.error(f"访问更新失败: {str(e)}", exc_info=True)
            await db.rollback()
            return 0


async def update_memory_access_in_background(
    db: AsyncSession,
    memory_ids: List[int]
):
    """
    异步后台任务：更新记忆访问统计

    Args:
        db: 数据库会话
        memory_ids: 被更新的记忆ID列表
    """
    try:
        await MemoryAccessUpdateService.update_memory_access(db, memory_ids)
    except Exception as e:
        logger.error(f"后台访问更新任务失败: {str(e)}", exc_info=True)
