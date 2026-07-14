"""二手 / 新房成交板块。成交即触发客户价值重估。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
from services import synergy_engine

router = APIRouter(prefix="/api/transactions", tags=["成交"])


@router.get("", response_model=List[schemas.TransactionOut])
def list_transactions(db: Session = Depends(get_db)):
    return db.query(models.Transaction).order_by(
        models.Transaction.deal_date.desc()).all()


@router.post("", response_model=schemas.TransactionOut)
def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db)):
    txn = models.Transaction(**payload.model_dump())
    db.add(txn)
    db.commit()
    db.refresh(txn)
    # 协同核心：成交 → 客户价值重估 → 可能升级进 VIP 漏斗
    if txn.client_id:
        synergy_engine.evaluate_and_upgrade_client(db, txn.client_id)
    return txn


@router.get("/stats")
def transaction_stats(db: Session = Depends(get_db)):
    """成交看板：总佣金、按区域分布。"""
    txns = db.query(models.Transaction).all()
    total_commission = sum(t.commission or 0 for t in txns)
    total_deal = sum(t.deal_price or 0 for t in txns)
    by_district = {}
    for t in txns:
        d = t.district or "未知"
        by_district.setdefault(d, {"count": 0, "commission": 0})
        by_district[d]["count"] += 1
        by_district[d]["commission"] += t.commission or 0
    return {
        "total_deal_count": len(txns),
        "total_deal_price": round(total_deal, 1),
        "total_commission": round(total_commission, 1),
        "by_district": by_district,
    }
