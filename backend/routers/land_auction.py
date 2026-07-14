"""土拍板块。新增土拍记录自动生成自媒体选题。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
from services import synergy_engine

router = APIRouter(prefix="/api/land-auctions", tags=["土拍市场"])


@router.get("", response_model=List[schemas.LandAuctionOut])
def list_auctions(db: Session = Depends(get_db)):
    return db.query(models.LandAuction).order_by(
        models.LandAuction.auction_date.desc()).all()


@router.post("", response_model=schemas.LandAuctionOut)
def create_auction(payload: schemas.LandAuctionCreate, db: Session = Depends(get_db)):
    auction = models.LandAuction(**payload.model_dump())
    db.add(auction)
    db.commit()
    db.refresh(auction)
    # 协同：土拍 → 自动选题
    synergy_engine.generate_topics_from_auction(db, auction)
    return auction
