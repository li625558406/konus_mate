"""
系统提示词服务
管理系统提示词的 CRUD 操作
"""
import logging
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_instruction import SystemInstruction
from app.schemas.system_instruction import SystemInstructionCreate, SystemInstructionUpdate, SystemInstructionResponse

logger = logging.getLogger(__name__)


class SystemInstructionService:
    """系统提示词服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SystemInstructionCreate) -> SystemInstructionResponse:
        """创建系统提示词"""
        # 如果设置为默认，取消其他默认设置
        if data.is_default:
            await self._clear_defaults()

        instruction = SystemInstruction(**data.model_dump())
        self.db.add(instruction)
        await self.db.commit()
        await self.db.refresh(instruction)
        return SystemInstructionResponse.model_validate(instruction)

    async def get_by_id(self, instruction_id: int) -> Optional[SystemInstructionResponse]:
        """根据 ID 获取系统提示词"""
        result = await self.db.execute(
            select(SystemInstruction).where(SystemInstruction.id == instruction_id)
        )
        instruction = result.scalar_one_or_none()
        if instruction:
            return SystemInstructionResponse.model_validate(instruction)
        return None

    async def get_default(self) -> Optional[SystemInstructionResponse]:
        """获取默认系统提示词"""
        result = await self.db.execute(
            select(SystemInstruction)
            .where(and_(SystemInstruction.is_default == True, SystemInstruction.is_active == True))
            .order_by(SystemInstruction.sort_order)
            .limit(1)
        )
        instruction = result.scalar_one_or_none()
        if instruction:
            return SystemInstructionResponse.model_validate(instruction)
        return None

    async def list_all(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SystemInstructionResponse]:
        """列出所有系统提示词"""
        query = select(SystemInstruction)

        if is_active is not None:
            query = query.where(SystemInstruction.is_active == is_active)

        query = query.order_by(SystemInstruction.sort_order).offset(skip).limit(limit)

        result = await self.db.execute(query)
        instructions = result.scalars().all()
        return [SystemInstructionResponse.model_validate(i) for i in instructions]

    async def update(
        self,
        instruction_id: int,
        data: SystemInstructionUpdate
    ) -> Optional[SystemInstructionResponse]:
        """更新系统提示词"""
        result = await self.db.execute(
            select(SystemInstruction).where(SystemInstruction.id == instruction_id)
        )
        instruction = result.scalar_one_or_none()

        if not instruction:
            return None

        # 如果设置为默认，取消其他默认设置
        if data.is_default and data.is_default != instruction.is_default:
            await self._clear_defaults()

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(instruction, field, value)

        await self.db.commit()
        await self.db.refresh(instruction)
        return SystemInstructionResponse.model_validate(instruction)

    async def delete(self, instruction_id: int) -> bool:
        """删除系统提示词"""
        result = await self.db.execute(
            select(SystemInstruction).where(SystemInstruction.id == instruction_id)
        )
        instruction = result.scalar_one_or_none()

        if not instruction:
            return False

        await self.db.delete(instruction)
        await self.db.commit()
        return True

    async def _clear_defaults(self) -> None:
        """清除所有默认标记"""
        result = await self.db.execute(
            select(SystemInstruction).where(SystemInstruction.is_default == True)
        )
        instructions = result.scalars().all()
        for instruction in instructions:
            instruction.is_default = False
