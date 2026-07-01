"""客户 / VIP 板块 + 客户360视图。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
from services import synergy_engine

router = APIRouter(prefix="/api/clients", tags=["客户/VIP"])


@router.get("", response_model=List[schemas.ClientOut])
def list_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).order_by(models.Client.value_score.desc()).all()


@router.post("", response_model=schemas.ClientOut)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    client = models.Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    # 入库即评分
    synergy_engine.evaluate_and_upgrade_client(db, client.id)
    db.refresh(client)
    return client


@router.get("/{client_id}/360", response_model=schemas.Client360)
def client_360(client_id: int, db: Session = Depends(get_db)):
    """客户360：聚合该客户在所有板块的足迹 + 跨板块推荐。"""
    client = db.query(models.Client).get(client_id)
    if not client:
        raise HTTPException(404, "客户不存在")
    txns = db.query(models.Transaction).filter(
        models.Transaction.client_id == client_id).all()
    meetings = db.query(models.Meeting).filter(
        models.Meeting.client_id == client_id).all()
    contracts = db.query(models.Contract).filter(
        models.Contract.client_id == client_id).all()
    recs = synergy_engine.recommend_cross_module(db, client)
    return schemas.Client360(
        client=client, transactions=txns, meetings=meetings,
        contracts=contracts, recommendations=recs,
    )


@router.post("/{client_id}/reevaluate", response_model=schemas.ClientOut)
def reevaluate(client_id: int, db: Session = Depends(get_db)):
    client = synergy_engine.evaluate_and_upgrade_client(db, client_id)
    if not client:
        raise HTTPException(404, "客户不存在")
    return client
