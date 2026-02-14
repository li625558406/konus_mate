"""
定时任务服务
使用APScheduler管理所有后台定时任务
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.db.session import AsyncSessionLocal
from app.services.cleanup_service import daily_memory_cleanup_in_background

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务管理服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        """启动所有定时任务"""
        logger.info("启动定时任务服务...")

        # 每天凌晨3点执行垃圾回收
        self.scheduler.add_job(
            self._daily_cleanup_task,
            trigger=CronTrigger(hour=3, minute=0),  # 每天凌晨3点
            id='daily_memory_cleanup',
            name='每日记忆垃圾回收',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("定时任务服务启动成功")

    async def stop(self):
        """停止所有定时任务"""
        logger.info("停止定时任务服务...")
        self.scheduler.shutdown()
        logger.info("定时任务服务已停止")

    async def _daily_cleanup_task(self):
        """每日记忆清理任务（后台异步执行）"""
        try:
            logger.info("开始执行每日记忆垃圾回收...")

            # 创建新的数据库会话
            async with AsyncSessionLocal() as db:
                # 执行异步清理
                await daily_memory_cleanup_in_background(db)

            logger.info("每日记忆垃圾回收完成")
        except Exception as e:
            logger.error(f"每日记忆清理任务失败: {str(e)}", exc_info=True)


# 全局scheduler实例
scheduler_service = SchedulerService()
