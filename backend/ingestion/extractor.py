"""抽取器：纯文本 → 结构化记录 → 入库 → 触发协同。

策略：用正则 + 关键词启发式从文本里抽出成交/土拍/房源字段。
真实场景可替换为 LLM 抽取（预留 extract_with_llm 接口），但规则版离线可跑。

用法（命令行批量入库一个文件夹）：
    python -m ingestion.extractor ./sample_inbox
"""
import os
import re
import sys

from database import SessionLocal, init_db
import models
from ingestion.parsers import parse_file
from services import synergy_engine

# 深圳常见区域关键词
DISTRICT_KEYWORDS = {
    "福田": ["福田", "香蜜湖", "车公庙", "竹子林", "皇岗"],
    "南山": ["南山", "后海", "前海", "深圳湾", "科技园", "蛇口"],
    "宝中": ["宝中", "宝安中心", "宝安", "海纳"],
}

MONEY_RE = re.compile(r"(\d+(?:\.\d+)?)\s*万")
AREA_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:平|㎡|平方米|m2)")
UNIT_RE = re.compile(r"(\d{4,6})\s*元?\s*/\s*(?:平|㎡|平方米)")
PREMIUM_RE = re.compile(r"溢价率?\s*[:：]?\s*(\d+(?:\.\d+)?)\s*%")
FLOOR_PRICE_RE = re.compile(r"楼面价\s*[:：]?\s*(\d+(?:\.\d+)?)")


def detect_district(text: str) -> str:
    for district, kws in DISTRICT_KEYWORDS.items():
        if any(kw in text for kw in kws):
            return district
    return ""


def classify(text: str) -> str:
    """判断这段文本主要是哪类业务数据。"""
    if "土拍" in text or "出让" in text or "楼面价" in text:
        return "土拍"
    if "成交" in text or "签约" in text or "佣金" in text:
        return "成交"
    if "在售" in text or "户型" in text or "豪宅" in text or "蓄客" in text:
        return "房源"
    return "未知"


def extract_records(text: str, source_doc: str) -> dict:
    """从文本抽出结构化记录（按块切分，每个非空段落尝试抽一条）。"""
    result = {"transactions": [], "auctions": [], "properties": []}
    blocks = [b.strip() for b in re.split(r"\n{1,}", text) if b.strip()]

    for block in blocks:
        kind = classify(block)
        district = detect_district(block)
        money = [float(m) for m in MONEY_RE.findall(block)]

        if kind == "土拍":
            floor = FLOOR_PRICE_RE.search(block)
            premium = PREMIUM_RE.search(block)
            result["auctions"].append({
                "district": district,
                "location": block[:30],
                "floor_price": float(floor.group(1)) if floor else None,
                "premium_rate": float(premium.group(1)) if premium else None,
                "note": block[:120],
                "source_doc": source_doc,
            })
        elif kind == "成交":
            deal_price = max(money) if money else 0
            # 佣金：取较小金额，或按 1% 估算
            commission = min(money) if len(money) >= 2 else round(deal_price * 0.01, 1)
            if deal_price:
                result["transactions"].append({
                    "deal_type": "二手" if "二手" in block else ("新房" if "新房" in block else "二手"),
                    "deal_price": deal_price,
                    "commission": commission,
                    "district": district,
                    "source_doc": source_doc,
                })
        elif kind == "房源":
            area = AREA_RE.search(block)
            unit = UNIT_RE.search(block)
            result["properties"].append({
                "name": block[:24],
                "district": district,
                "category": "豪宅" if "豪宅" in block else "二手",
                "area": float(area.group(1)) if area else None,
                "total_price": max(money) if money else None,
                "unit_price": float(unit.group(1)) if unit else None,
                "source_doc": source_doc,
            })
    return result


def ingest_text(db, text: str, source_doc: str) -> dict:
    """把抽取结果写库，并触发协同（土拍→选题、成交→客户评分）。"""
    records = extract_records(text, source_doc)
    stats = {"transactions": 0, "auctions": 0, "properties": 0}

    for a in records["auctions"]:
        auction = models.LandAuction(**a)
        db.add(auction)
        db.commit()
        db.refresh(auction)
        synergy_engine.generate_topics_from_auction(db, auction)  # 协同：自动选题
        stats["auctions"] += 1

    for p in records["properties"]:
        prop = models.Property(**p)
        db.add(prop)
        db.commit()
        db.refresh(prop)
        if prop.category == "豪宅":
            synergy_engine.generate_topic_from_property(db, prop)  # 协同：看房选题
        stats["properties"] += 1

    for t in records["transactions"]:
        txn = models.Transaction(**t)
        db.add(txn)
        db.commit()
        stats["transactions"] += 1

    return stats


def ingest_folder(folder: str):
    """批量处理一个文件夹里的所有 pdf/docx/pptx。"""
    init_db()
    db = SessionLocal()
    total = {"transactions": 0, "auctions": 0, "properties": 0, "files": 0}
    try:
        for fname in os.listdir(folder):
            path = os.path.join(folder, fname)
            if not os.path.isfile(path):
                continue
            if os.path.splitext(fname)[1].lower() not in (".pdf", ".docx", ".doc", ".pptx", ".ppt"):
                continue
            print(f"解析：{fname}")
            text = parse_file(path)
            if not text.strip():
                continue
            stats = ingest_text(db, text, fname)
            total["files"] += 1
            for k in ("transactions", "auctions", "properties"):
                total[k] += stats[k]
            print(f"  → 成交{stats['transactions']} 土拍{stats['auctions']} 房源{stats['properties']}")
    finally:
        db.close()
    print("\n入库完成：", total)
    return total


def extract_with_llm(text: str) -> dict:
    """预留：用 LLM 做更鲁棒的字段抽取（输入文本，返回结构化 dict）。"""
    raise NotImplementedError("接入 LLM 后实现")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "./sample_inbox"
    if not os.path.isdir(target):
        print(f"目录不存在：{target}\n用法：python -m ingestion.extractor <文件夹>")
        sys.exit(1)
    ingest_folder(target)
