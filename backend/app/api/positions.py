"""
职位配置API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.position import PositionConfig
from app.schemas.position import (
    PositionCreate,
    PositionUpdate,
    PositionResponse,
    PositionListResponse,
)

router = APIRouter(prefix="/api/positions", tags=["职位配置"])


@router.get("/", response_model=PositionListResponse)
async def list_positions(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
):
    """获取职位配置列表"""
    query = db.query(PositionConfig)

    # 筛选条件
    if is_active is not None:
        query = query.filter(PositionConfig.is_active == is_active)
    if keyword:
        query = query.filter(PositionConfig.title.ilike(f"%{keyword}%"))

    # 获取总数
    total = query.count()

    # 分页查询
    positions = query.order_by(PositionConfig.created_at.desc()).offset(skip).limit(limit).all()

    return PositionListResponse(
        items=[PositionResponse.from_orm(p) for p in positions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: str,
    db: Session = Depends(get_db),
):
    """获取单个职位配置详情"""
    position = db.query(PositionConfig).filter(PositionConfig.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="职位配置不存在")
    return PositionResponse.from_orm(position)


@router.post("/", response_model=PositionResponse)
async def create_position(
    position_data: PositionCreate,
    db: Session = Depends(get_db),
):
    """创建职位配置"""
    try:
        # 将list转换为JSON字符串
        import json
        data = position_data.model_dump()
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = json.dumps(value, ensure_ascii=False)

        # 创建职位配置
        position = PositionConfig(**data)
        db.add(position)
        db.commit()
        db.refresh(position)

        return PositionResponse.from_orm(position)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{position_id}", response_model=PositionResponse)
async def update_position(
    position_id: str,
    position_data: PositionUpdate,
    db: Session = Depends(get_db),
):
    """更新职位配置"""
    position = db.query(PositionConfig).filter(PositionConfig.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="职位配置不存在")

    # 更新字段
    update_data = position_data.dict(exclude_unset=True)
    import json
    for key, value in update_data.items():
        if isinstance(value, list):
            value = json.dumps(value, ensure_ascii=False)
        setattr(position, key, value)

    db.commit()
    db.refresh(position)

    return PositionResponse.from_orm(position)


@router.delete("/{position_id}")
async def delete_position(
    position_id: str,
    db: Session = Depends(get_db),
):
    """删除职位配置（软删除）"""
    position = db.query(PositionConfig).filter(PositionConfig.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="职位配置不存在")

    # 软删除
    position.is_active = False
    db.commit()

    return {"message": "职位配置已禁用"}


@router.patch("/{position_id}/enable")
async def enable_position(
    position_id: str,
    db: Session = Depends(get_db),
):
    """启用职位配置"""
    position = db.query(PositionConfig).filter(PositionConfig.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="职位配置不存在")

    position.is_active = True
    db.commit()

    return {"message": "职位配置已启用"}


@router.delete("/{position_id}/hard")
async def hard_delete_position(
    position_id: str,
    db: Session = Depends(get_db),
):
    """彻底删除职位配置（硬删除）"""
    position = db.query(PositionConfig).filter(PositionConfig.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="职位配置不存在")

    db.delete(position)
    db.commit()

    return {"message": "职位配置已彻底删除"}
