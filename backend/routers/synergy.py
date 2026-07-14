"""协同板块：区域情报、协同事件日志、总览看板。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
from services import synergy_engine

router = APIRouter(prefix="/api/synergy", tags=["协同引擎"])


@router.get("/district-intelligence")
def district_intelligence(db: Session = Depends(get_db)):
    """福田/南山/宝中 区域情报卡（聚合成交+在售+土拍，给调价/选题建议）。"""
    return synergy_engine.district_intelligence(db)


@router.get("/events", response_model=List[schemas.SynergyEventOut])
def synergy_events(db: Session = Depends(get_db)):
    """协同事件流：引擎自动串联板块的每一个动作。"""
    return db.query(models.SynergyEvent).order_by(
        models.SynergyEvent.created_at.desc()).limit(100).all()


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """全局总览看板。"""
    txns = db.query(models.Transaction).all()
    clients = db.query(models.Client).all()
    contents = db.query(models.Content).all()
    return {
        "client_count": len(clients),
        "vip_count": sum(1 for c in clients if c.level == "VIP"),
        "high_value_count": sum(1 for c in clients if c.level == "高净值"),
        "deal_count": len(txns),
        "total_commission": round(sum(t.commission or 0 for t in txns), 1),
        "total_deal_price": round(sum(t.deal_price or 0 for t in txns), 1),
        "content_count": len(contents),
        "auto_content_count": sum(1 for c in contents if c.auto_generated),
        "auction_count": db.query(models.LandAuction).count(),
        "meeting_count": db.query(models.Meeting).count(),
        "synergy_event_count": db.query(models.SynergyEvent).count(),
    }
