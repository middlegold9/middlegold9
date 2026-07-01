"""房源 / 楼盘板块。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
import models
import schemas
from services import synergy_engine

router = APIRouter(prefix="/api/properties", tags=["房源/楼盘"])


@router.get("", response_model=List[schemas.PropertyOut])
def list_properties(district: Optional[str] = None, category: Optional[str] = None,
                    db: Session = Depends(get_db)):
    q = db.query(models.Property)
    if district:
        q = q.filter(models.Property.district == district)
    if category:
        q = q.filter(models.Property.category == category)
    return q.all()


@router.post("", response_model=schemas.PropertyOut)
def create_property(payload: schemas.PropertyCreate, db: Session = Depends(get_db)):
    prop = models.Property(**payload.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    # 协同：豪宅/新房自动产看房选题
    if prop.category in ("豪宅", "新房"):
        synergy_engine.generate_topic_from_property(db, prop)
    return prop
