"""
系统提示词 API 路由
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.system_instruction import (
    SystemInstructionCreate,
    SystemInstructionResponse,
    SystemInstructionUpdate,
)
from app.services.system_instruction_service import SystemInstructionService
from app.api.dependencies import get_system_instruction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system-instructions", tags=["系统提示词"])


@router.post("", response_model=SystemInstructionResponse, status_code=status.HTTP_201_CREATED, summary="创建系统提示词")
async def create_system_instruction(
    data: SystemInstructionCreate,
    service: SystemInstructionService = Depends(get_system_instruction_service),
):
    """创建新的系统提示词"""
    try:
        return await service.create(data)
    except Exception as e:
        logger.error(f"Failed to create system instruction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.get("/default", response_model=SystemInstructionResponse, summary="获取默认系统提示词")
async def get_default_system_instruction(
    service: SystemInstructionService = Depends(get_system_instruction_service),
):
    """获取默认的系统提示词"""
    instruction = await service.get_default()
    if not instruction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到默认系统提示词"
        )
    return instruction


@router.get("/{instruction_id}", response_model=SystemInstructionResponse, summary="获取系统提示词")
async def get_system_instruction(
    instruction_id: int,
    service: SystemInstructionService = Depends(get_system_instruction_service),
):
    """根据 ID 获取系统提示词"""
    instruction = await service.get_by_id(instruction_id)
    if not instruction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统提示词不存在"
        )
    return instruction


@router.get("", response_model=List[SystemInstructionResponse], summary="获取系统提示词列表")
async def list_system_instructions(
    is_active: bool = Query(None, description="筛选启用状态"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=100, description="返回数量"),
    service: SystemInstructionService = Depends(get_system_instruction_service),
):
    """获取系统提示词列表"""
    return await service.list_all(is_active=is_active, skip=skip, limit=limit)


@router.put("/{instruction_id}", response_model=SystemInstructionResponse, summary="更新系统提示词")
async def update_system_instruction(
    instruction_id: int,
    data: SystemInstructionUpdate,
    service: SystemInstructionService = Depends(get_system_instruction_service),
):
    """更新系统提示词"""
    instruction = await service.update(instruction_id, data)
    if not instruction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统提示词不存在"
        )
    return instruction


@router.delete("/{instruction_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除系统提示词")
async def delete_system_instruction(
    instruction_id: int,
    service: SystemInstructionService = Depends(get_system_instruction_service),
):
    """删除系统提示词"""
    success = await service.delete(instruction_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统提示词不存在"
        )
