"""自媒体内容板块（豪宅看房 / 土拍分析）+ 引流线索。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/contents", tags=["自媒体内容"])


@router.get("", response_model=List[schemas.ContentOut])
def list_contents(db: Session = Depends(get_db)):
    return db.query(models.Content).order_by(models.Content.created_at.desc()).all()


@router.post("", response_model=schemas.ContentOut)
def create_content(payload: schemas.ContentCreate, db: Session = Depends(get_db)):
    content = models.Content(**payload.model_dump())
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


@router.get("/pipeline")
def content_pipeline(db: Session = Depends(get_db)):
    """内容流水线看板：选题/拍摄中/已发布 + 自动生成占比。"""
    contents = db.query(models.Content).all()
    pipeline = {"选题": [], "拍摄中": [], "已发布": []}
    for c in contents:
        pipeline.setdefault(c.status, []).append({
            "id": c.id, "title": c.title, "category": c.category,
            "auto": bool(c.auto_generated), "leads": c.leads_count,
        })
    auto_count = sum(1 for c in contents if c.auto_generated)
    return {
        "pipeline": pipeline,
        "total": len(contents),
        "auto_generated": auto_count,
        "total_leads": sum(c.leads_count or 0 for c in contents),
    }
