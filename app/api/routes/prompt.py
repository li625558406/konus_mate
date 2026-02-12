"""
Prompt API 路由
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.prompt import PromptCreate, PromptResponse, PromptUpdate
from app.services.prompt_service import PromptService
from app.api.dependencies import get_prompt_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompts", tags=["Prompt"])


@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED, summary="创建 Prompt")
async def create_prompt(
    data: PromptCreate,
    service: PromptService = Depends(get_prompt_service),
):
    """创建新的 Prompt"""
    try:
        return await service.create(data)
    except Exception as e:
        logger.error(f"Failed to create prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.get("/default", response_model=PromptResponse, summary="获取默认 Prompt")
async def get_default_prompt(
    service: PromptService = Depends(get_prompt_service),
):
    """获取默认的 Prompt"""
    prompt = await service.get_default()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到默认 Prompt"
        )
    return prompt


@router.get("/{prompt_id}", response_model=PromptResponse, summary="获取 Prompt")
async def get_prompt(
    prompt_id: int,
    service: PromptService = Depends(get_prompt_service),
):
    """根据 ID 获取 Prompt"""
    prompt = await service.get_by_id(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt 不存在"
        )
    return prompt


@router.get("", response_model=List[PromptResponse], summary="获取 Prompt 列表")
async def list_prompts(
    is_active: bool = Query(None, description="筛选启用状态"),
    category: str = Query(None, description="筛选分类"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=100, description="返回数量"),
    service: PromptService = Depends(get_prompt_service),
):
    """获取 Prompt 列表"""
    return await service.list_all(is_active=is_active, category=category, skip=skip, limit=limit)


@router.put("/{prompt_id}", response_model=PromptResponse, summary="更新 Prompt")
async def update_prompt(
    prompt_id: int,
    data: PromptUpdate,
    service: PromptService = Depends(get_prompt_service),
):
    """更新 Prompt"""
    prompt = await service.update(prompt_id, data)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt 不存在"
        )
    return prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除 Prompt")
async def delete_prompt(
    prompt_id: int,
    service: PromptService = Depends(get_prompt_service),
):
    """删除 Prompt"""
    success = await service.delete(prompt_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt 不存在"
        )
