"""
异步记忆清理服务
替代同步脚本，统一使用异步架构
"""
import time
import logging
from typing import List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class CleanupService:
    """异步清理服务 - 使用异步数据库操作"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def daily_memory_cleanup_async(self) -> int:
        """
        异步每日记忆清理

        清理规则（统一）：
        1. 短期垃圾（event/desire，7天未访问 + 情绪低）
        2. 冷数据清理（所有类型，30天未访问 + 访问少）

        Args:
            None

        Returns:
            删除的记录数
        """
        try:
            current_time = int(time.time())
            seconds_per_day = 86400

            logger.info("=" * 70)
            logger.info("异步记忆垃圾回收：清理旧记忆（软删除）")
            logger.info("=" * 70)

            # ========== 1. 查询需要检查的记忆 ==========
            logger.info(f"\n[步骤 1] 查找需要检查的记忆...")
            logger.info(f"当前时间戳：{current_time} ({time.ctime(current_time)})")

            # 查询所有 event 和 desire 类型的记忆
            result = await self.db.execute(
                select(ConversationMemory)
                .where(
                    and_(
                        ConversationMemory.memory_category.in_(['event', 'desire']),
                        ConversationMemory.is_deleted == False
                    )
                )
                .order_by(ConversationMemory.created_at_timestamp.desc())
            )
            memories = result.scalars().all()
            logger.info(f"  找到 {len(memories)} 条临时记忆")

            if not memories:
                logger.info("  没有需要处理的记忆")
                return 0

            # ========== 2. 判断清理规则（考虑重要性）==========
            ids_to_soft_delete = []

            for mem in memories:
                mem_id = mem.id
                mem_category = mem.memory_category or "event"
                created_at = mem.created_at_timestamp or current_time
                last_accessed = mem.last_accessed or created_at
                access_count = mem.access_count or 1
                emotional_weight = mem.emotional_weight or 0.5
                importance_score = mem.importance_score or 5
                summary = mem.summary[:50] if mem.summary else ""

                # 计算未访问天数
                days_since_access = (current_time - last_accessed) / seconds_per_day

                # ========== 清理规则（统一，添加重要性判断）==========

                # 规则1：短期垃圾（event/desire，7天未访问 + 情绪低 + 重要性低）
                if (mem_category in ['event', 'desire'] and
                    days_since_access > 7 and
                    emotional_weight < 0.5 and
                    importance_score < 5):
                    ids_to_soft_delete.append(mem_id)
                    logger.info(f"  [SOFT_DELETE] ID={mem_id}: {days_since_access:.1f}天未访问, "
                                    f"情绪={emotional_weight:.2f}, 重要性={importance_score}/10 - {summary}")
                    continue

                # 规则2：冷数据清理（所有类型，30天未访问 + 访问少 + 重要性低）
                if days_since_access > 30 and access_count < 3 and importance_score < 5:
                    ids_to_soft_delete.append(mem_id)
                    logger.info(f"  [SOFT_DELETE] ID={mem_id}: {days_since_access:.1f}天未访问, "
                                    f"访问{access_count}次, 重要性={importance_score}/10 - {summary}")
                    continue

            # ========== 3. 执行批量软删除 ==========
            logger.info(f"\n[步骤 2] 执行清理...")
            if ids_to_soft_delete:
                # 软删除（更新 is_deleted 和 deleted_at 字段）
                current_timestamp = int(time.time())

                # 使用批量UPDATE进行软删除
                from sqlalchemy import update
                await self.db.execute(
                    update(ConversationMemory)
                    .where(ConversationMemory.id.in_(ids_to_soft_delete))
                    .values(
                        is_deleted=True,
                        deleted_at=datetime.now(timezone.utc)
                    )
                )

                await self.db.commit()
                logger.info(f"  ✓ 已软删除 {len(ids_to_soft_delete)} 条记忆")
            else:
                logger.info("  没有需要删除的记忆")

            # ========== 4. 统计 ==========
            total_processed = len(ids_to_soft_delete)
            logger.info("\n" + "=" * 70)
            logger.info(f"垃圾回收完成！共处理 {total_processed} 条记忆")
            logger.info("=" * 70)

            return total_processed

        except Exception as e:
            logger.error(f"\n[错误] 垃圾回收失败: {str(e)}", exc_info=True)
            await self.db.rollback()
            return 0


async def daily_memory_cleanup_in_background(
    db: AsyncSession
):
    """
    异步后台任务：每日记忆清理
    """
    try:
        service = CleanupService(db)
        await service.daily_memory_cleanup_async()
    except Exception as e:
        logger.error(f"后台清理任务失败: {str(e)}", exc_info=True)
