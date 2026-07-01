"""VIP 会面板块。创建会面自动生成会面 brief（拉全板块画像）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
from services import synergy_engine

router = APIRouter(prefix="/api/meetings", tags=["客户会面"])


@router.get("", response_model=List[schemas.MeetingOut])
def list_meetings(db: Session = Depends(get_db)):
    return db.query(models.Meeting).order_by(models.Meeting.meet_date).all()


@router.post("", response_model=schemas.MeetingOut)
def create_meeting(payload: schemas.MeetingCreate, db: Session = Depends(get_db)):
    meeting = models.Meeting(**payload.model_dump())
    # 协同：自动生成会面 brief
    meeting.brief = synergy_engine.build_meeting_brief(db, payload.client_id)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("/{meeting_id}/brief")
def get_brief(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(models.Meeting).get(meeting_id)
    if not meeting:
        raise HTTPException(404, "会面不存在")
    # 实时重新生成（数据可能已更新）
    brief = synergy_engine.build_meeting_brief(db, meeting.client_id)
    meeting.brief = brief
    db.commit()
    return {"meeting_id": meeting_id, "brief": brief}
