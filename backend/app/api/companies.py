"""
公司管理API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.company import Company
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
)

router = APIRouter(prefix="/api/companies", tags=["公司管理"])


@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
):
    """获取公司列表"""
    query = db.query(Company)

    # 筛选条件
    if is_active is not None:
        query = query.filter(Company.is_active == is_active)
    if keyword:
        query = query.filter(
            Company.name.ilike(f"%{keyword}%") |
            Company.industry.ilike(f"%{keyword}%")
        )

    # 获取总数
    total = query.count()

    # 分页查询
    companies = query.order_by(Company.created_at.desc()).offset(skip).limit(limit).all()

    return CompanyListResponse(
        items=[CompanyResponse.from_orm(c) for c in companies],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    db: Session = Depends(get_db),
):
    """获取单个公司详情"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return CompanyResponse.from_orm(company)


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
):
    """创建公司"""
    try:
        # 检查名称是否重复
        existing = db.query(Company).filter(Company.name == company_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="公司名称已存在")

        # 创建公司，将list转换为JSON字符串
        import json
        data = company_data.model_dump()
        # 将所有list字段转换为JSON字符串
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = json.dumps(value, ensure_ascii=False)

        company = Company(**data)
        db.add(company)
        db.commit()
        db.refresh(company)

        return CompanyResponse.from_orm(company)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    db: Session = Depends(get_db),
):
    """更新公司"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    # 更新字段
    update_data = company_data.dict(exclude_unset=True)
    import json
    for key, value in update_data.items():
        if isinstance(value, list):
            value = json.dumps(value, ensure_ascii=False)
        setattr(company, key, value)

    db.commit()
    db.refresh(company)

    return CompanyResponse.from_orm(company)


@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    db: Session = Depends(get_db),
):
    """删除公司（软删除）"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    # 软删除
    company.is_active = False
    db.commit()

    return {"message": "公司已禁用"}


@router.patch("/{company_id}/enable")
async def enable_company(
    company_id: str,
    db: Session = Depends(get_db),
):
    """启用公司"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    company.is_active = True
    db.commit()

    return {"message": "公司已启用"}


@router.delete("/{company_id}/hard")
async def hard_delete_company(
    company_id: str,
    db: Session = Depends(get_db),
):
    """彻底删除公司（硬删除）"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    db.delete(company)
    db.commit()

    return {"message": "公司已彻底删除"}
