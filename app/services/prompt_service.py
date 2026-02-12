"""
Prompt 服务
管理 Prompt 的 CRUD 操作
"""
import logging
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse

logger = logging.getLogger(__name__)


class PromptService:
    """Prompt 服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: PromptCreate) -> PromptResponse:
        """创建 Prompt"""
        # 如果设置为默认，取消其他默认设置
        if data.is_default:
            await self._clear_defaults()

        prompt = Prompt(**data.model_dump())
        self.db.add(prompt)
        await self.db.commit()
        await self.db.refresh(prompt)
        return PromptResponse.model_validate(prompt)

    async def get_by_id(self, prompt_id: int) -> Optional[PromptResponse]:
        """根据 ID 获取 Prompt"""
        result = await self.db.execute(
            select(Prompt).where(Prompt.id == prompt_id)
        )
        prompt = result.scalar_one_or_none()
        if prompt:
            return PromptResponse.model_validate(prompt)
        return None

    async def get_default(self) -> Optional[PromptResponse]:
        """获取默认 Prompt"""
        result = await self.db.execute(
            select(Prompt)
            .where(and_(Prompt.is_default == True, Prompt.is_active == True))
            .order_by(Prompt.sort_order)
            .limit(1)
        )
        prompt = result.scalar_one_or_none()
        if prompt:
            return PromptResponse.model_validate(prompt)
        return None

    async def list_all(
        self,
        is_active: Optional[bool] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[PromptResponse]:
        """列出所有 Prompt"""
        query = select(Prompt)

        if is_active is not None:
            query = query.where(Prompt.is_active == is_active)

        if category:
            query = query.where(Prompt.category == category)

        query = query.order_by(Prompt.sort_order).offset(skip).limit(limit)

        result = await self.db.execute(query)
        prompts = result.scalars().all()
        return [PromptResponse.model_validate(p) for p in prompts]

    async def update(
        self,
        prompt_id: int,
        data: PromptUpdate
    ) -> Optional[PromptResponse]:
        """更新 Prompt"""
        result = await self.db.execute(
            select(Prompt).where(Prompt.id == prompt_id)
        )
        prompt = result.scalar_one_or_none()

        if not prompt:
            return None

        # 如果设置为默认，取消其他默认设置
        if data.is_default and data.is_default != prompt.is_default:
            await self._clear_defaults()

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prompt, field, value)

        await self.db.commit()
        await self.db.refresh(prompt)
        return PromptResponse.model_validate(prompt)

    async def delete(self, prompt_id: int) -> bool:
        """删除 Prompt"""
        result = await self.db.execute(
            select(Prompt).where(Prompt.id == prompt_id)
        )
        prompt = result.scalar_one_or_none()

        if not prompt:
            return False

        await self.db.delete(prompt)
        await self.db.commit()
        return True

    async def _clear_defaults(self) -> None:
        """清除所有默认标记"""
        result = await self.db.execute(
            select(Prompt).where(Prompt.is_default == True)
        )
        prompts = result.scalars().all()
        for prompt in prompts:
            prompt.is_default = False
