"""灌入示例数据，让系统开箱即用、能直接演示协同效应。

运行：python seed_data.py
"""
from datetime import datetime, timedelta

from database import SessionLocal, init_db, engine, Base
import models
from services import synergy_engine, contract_generator


def reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def run():
    reset()
    db = SessionLocal()
    try:
        # ---------- 客户 ----------
        c1 = models.Client(
            name="陈总", phone="138****8888", source="视频号", level="普通",
            net_worth_estimate=8000,
            needs={"理财": False, "保险": False, "香港身份": False, "子女教育": False},
            tags=["改善", "豪宅意向"], interest_districts=["南山", "福田"],
            note="深圳湾豪宅意向，做实业，有香港业务往来。",
        )
        c2 = models.Client(
            name="李女士", phone="139****6666", source="转介绍", level="普通",
            net_worth_estimate=2500, needs={"保险": False, "子女教育": False},
            tags=["学区"], interest_districts=["福田"],
            note="关注福田香蜜湖学区，孩子明年入学。",
        )
        c3 = models.Client(
            name="王先生", phone="135****2222", source="抖音", level="普通",
            net_worth_estimate=1200, needs={}, tags=["首置"],
            interest_districts=["宝中"], note="宝中刚需首置。",
        )
        db.add_all([c1, c2, c3])
        db.commit()
        for c in (c1, c2, c3):
            db.refresh(c)

        # ---------- 房源 ----------
        p1 = models.Property(
            name="深圳湾1号", district="南山", block="后海", category="豪宅",
            area=260, total_price=9800, unit_price=377000, status="在售",
            selling_points=["一线海景", "顶级会所", "稀缺大平层"], source_doc="豪宅清单.pptx",
        )
        p2 = models.Property(
            name="香蜜湖某花园", district="福田", block="香蜜湖", category="二手",
            area=120, total_price=2300, unit_price=191000, status="在售",
            selling_points=["名校学区", "地铁口"], source_doc="二手房源.xlsx",
        )
        p3 = models.Property(
            name="宝中海纳公馆", district="宝中", block="宝安中心", category="新房",
            area=89, total_price=950, unit_price=106700, status="在售",
            selling_points=["地铁上盖", "总价友好"], source_doc="新房备案.pdf",
        )
        db.add_all([p1, p2, p3])
        db.commit()
        for p in (p1, p2, p3):
            db.refresh(p)

        # ---------- 成交（触发客户评分/升级）----------
        t1 = models.Transaction(
            client_id=c1.id, property_id=p1.id, deal_type="二手",
            deal_price=9800, commission=98, district="南山",
            deal_date=datetime.now() - timedelta(days=10), source_doc="成交确认书.pdf",
        )
        t2 = models.Transaction(
            client_id=c2.id, property_id=p2.id, deal_type="二手",
            deal_price=2300, commission=23, district="福田",
            deal_date=datetime.now() - timedelta(days=5), source_doc="成交确认书.pdf",
        )
        t3 = models.Transaction(
            client_id=c3.id, property_id=p3.id, deal_type="新房",
            deal_price=950, commission=9.5, district="宝中",
            deal_date=datetime.now() - timedelta(days=2), source_doc="认购书.docx",
        )
        db.add_all([t1, t2, t3])
        db.commit()
        for t in (t1, t2, t3):
            db.refresh(t)

        # 触发协同：成交 → 客户评分升级
        for c in (c1, c2, c3):
            synergy_engine.evaluate_and_upgrade_client(db, c.id)

        # ---------- 土拍（触发自动选题）----------
        a1 = models.LandAuction(
            parcel_no="A001-0123", district="南山", location="后海中心区",
            floor_price=85000, premium_rate=22.5, winner="某央企",
            note="后海最后一块商住地，溢价率22.5%，楼面价创新高。",
            source_doc="土拍纪要.pdf",
        )
        a2 = models.LandAuction(
            parcel_no="B002-0456", district="宝中", location="宝安中心海纳片区",
            floor_price=55000, premium_rate=8.0, winner="某民企",
            note="宝中底价成交。", source_doc="土拍纪要.pdf",
        )
        db.add_all([a1, a2])
        db.commit()
        for a in (a1, a2):
            db.refresh(a)
            synergy_engine.generate_topics_from_auction(db, a)

        # 豪宅看房选题
        synergy_engine.generate_topic_from_property(db, p1)

        # ---------- 会面（自动生成 brief）----------
        m1 = models.Meeting(
            client_id=c1.id, meet_date=datetime.now() + timedelta(days=2),
            location="香格里拉酒店茶室", agenda="资产配置 + 香港身份规划", status="待确认",
        )
        m1.brief = synergy_engine.build_meeting_brief(db, c1.id)
        db.add(m1)
        db.commit()

        # ---------- 合同（基于成交自动生成）----------
        contract_generator.generate_contract(db, t1.id, "二手买卖")
        contract_generator.generate_contract(db, t1.id, "资产配置顾问")

        # ---------- 引流线索 ----------
        contents = db.query(models.Content).limit(2).all()
        if contents:
            db.add(models.Lead(
                name="抖音粉丝-海景房意向", channel="抖音私信",
                district_interest="南山", score=60, status="待跟进",
                from_content_id=contents[0].id,
            ))
        db.commit()

        print("=" * 50)
        print("示例数据灌入完成！")
        clients = db.query(models.Client).all()
        for c in clients:
            print(f"  客户 {c.name}: {c.level} (价值分 {c.value_score})")
        print(f"  自动生成内容选题：{db.query(models.Content).filter(models.Content.auto_generated==1).count()} 条")
        print(f"  协同事件：{db.query(models.SynergyEvent).count()} 条")
        print(f"  合同草稿：{db.query(models.Contract).count()} 份")
        print("=" * 50)
        print("启动后端：uvicorn main:app --reload --port 8000")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    run()
