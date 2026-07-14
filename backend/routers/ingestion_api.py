"""文档上传入库 API：把散落的 PDF/Word/PPT 通过接口上传即自动结构化。"""
import os
import tempfile

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from ingestion.parsers import parse_file
from ingestion.extractor import ingest_text

router = APIRouter(prefix="/api/ingestion", tags=["文档入库"])

ALLOWED = (".pdf", ".docx", ".doc", ".pptx", ".ppt")


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传单个文档 → 解析 → 抽取 → 入库 → 触发协同。"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED:
        return {"error": f"不支持的格式：{ext}，仅支持 {ALLOWED}"}

    # 写临时文件再解析（避免把上传内容直接当路径，规避路径穿越）
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        text = parse_file(tmp_path)
        if not text.strip():
            return {"filename": file.filename, "warning": "未解析出文本内容"}
        stats = ingest_text(db, text, file.filename or "uploaded")
    finally:
        os.unlink(tmp_path)

    return {"filename": file.filename, "ingested": stats}
