"""合同板块。基于成交记录一键生成合同草稿。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
from services import contract_generator

router = APIRouter(prefix="/api/contracts", tags=["合同"])


@router.get("", response_model=List[schemas.ContractOut])
def list_contracts(db: Session = Depends(get_db)):
    return db.query(models.Contract).order_by(models.Contract.created_at.desc()).all()


@router.post("/generate", response_model=schemas.ContractOut)
def generate(transaction_id: int, contract_type: str = "二手买卖",
             db: Session = Depends(get_db)):
    try:
        return contract_generator.generate_contract(db, transaction_id, contract_type)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{contract_id}", response_model=schemas.ContractOut)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    c = db.query(models.Contract).get(contract_id)
    if not c:
        raise HTTPException(404, "合同不存在")
    return c
