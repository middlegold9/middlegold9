"""协同引擎 —— 把 7 个孤立板块串成一张网。

这是整个 FDE 项目的核心价值：每个板块产生的信号，都会自动触发其它板块的动作。
全部用规则实现，离线可跑；预留 LLM 接口（generate_topic_with_llm）便于增强。

四类协同规则：
  1. 客户价值评分 & 自动升级（成交/资产 → VIP 漏斗）
  2. 土拍/成交热点 → 自动生成自媒体选题
  3. 区域情报聚合（福田/南山/宝中）→ 调价提示
  4. VIP 会面 brief 自动生成（拉全板块画像）
"""
from sqlalchemy.orm import Session
from datetime import datetime
import models


# ----------------------------------------------------------------------------
# 规则 1：客户价值评分 + 自动升级到 VIP 资产配置漏斗
# ----------------------------------------------------------------------------
def score_client(db: Session, client: models.Client) -> float:
    """根据成交额、需求广度、净资产计算客户价值分（0-100）。"""
    score = 0.0

    # 成交贡献（佣金是核心现金流，权重最高）
    txns = db.query(models.Transaction).filter(
        models.Transaction.client_id == client.id).all()
    total_deal = sum(t.deal_price or 0 for t in txns)
    score += min(total_deal / 1000 * 30, 40)  # 每千万成交 +30，封顶 40

    # 净资产
    score += min((client.net_worth_estimate or 0) / 5000 * 20, 25)

    # 跨板块需求广度（理财/保险/香港身份/子女教育，越多越粘）
    needs = client.needs or {}
    need_count = sum(1 for v in needs.values() if v)
    score += need_count * 6  # 每多一个需求 +6

    # 多区域兴趣（改善型/投资型客户）
    score += min(len(client.interest_districts or []) * 3, 9)

    return round(min(score, 100), 1)


def evaluate_and_upgrade_client(db: Session, client_id: int):
    """重新评分并按阈值自动升级客户等级，写协同日志。"""
    client = db.query(models.Client).get(client_id)
    if not client:
        return None

    old_level = client.level
    client.value_score = score_client(db, client)

    # 自动分级
    if client.value_score >= 70:
        client.level = "VIP"
    elif client.value_score >= 40:
        client.level = "高净值"
    else:
        client.level = "普通"

    if client.level != old_level and client.level in ("高净值", "VIP"):
        _log(
            db, "客户升级", "二手成交/资产", "VIP资产配置",
            f"客户「{client.name}」价值分 {client.value_score} 分，"
            f"由「{old_level}」升级为「{client.level}」，已推入 VIP 资产配置漏斗。",
            ref_client_id=client.id,
        )
        # 升级即提示补全资产配置需求
        if not (client.needs or {}):
            client.needs = {"理财": False, "保险": False,
                            "香港身份": False, "子女教育": False}

    db.commit()
    db.refresh(client)
    return client


# ----------------------------------------------------------------------------
# 规则 2：土拍 / 成交热点 → 自动生成自媒体选题
# ----------------------------------------------------------------------------
def generate_topics_from_auction(db: Session, auction: models.LandAuction):
    """一条土拍记录 → 1~2 个内容选题（土拍分析 + 区域解读）。"""
    created = []

    title1 = (f"【土拍快报】{auction.district}{auction.location} 楼面价 "
              f"{int(auction.floor_price or 0)}元/㎡，溢价率{auction.premium_rate or 0}%，"
              f"对周边房价意味着什么？")
    c1 = models.Content(
        title=title1, category="土拍分析", platform="视频号",
        status="选题", related_auction_id=auction.id, auto_generated=1,
    )
    db.add(c1)
    created.append(title1)

    # 若溢价率高，追加一个区域解读选题（更易爆）
    if (auction.premium_rate or 0) >= 15:
        title2 = (f"{auction.district}又上演抢地大战！起底{auction.location}"
                  f"未来3年新房供应与价格预期")
        c2 = models.Content(
            title=title2, category="区域解读", platform="抖音",
            status="选题", related_auction_id=auction.id, auto_generated=1,
        )
        db.add(c2)
        created.append(title2)

    _log(db, "选题生成", "土拍市场", "自媒体内容",
         f"土拍「{auction.location}」触发自动生成 {len(created)} 条选题。")
    db.commit()
    return created


def generate_topic_from_property(db: Session, prop: models.Property):
    """豪宅 / 新盘 → 看房选题。"""
    if prop.category not in ("豪宅", "新房"):
        return None
    points = "、".join(prop.selling_points or []) or "稀缺地段"
    title = f"【实探】{prop.district}{prop.block or ''}·{prop.name}：{points}，总价{int(prop.total_price or 0)}万起"
    c = models.Content(
        title=title, category="豪宅看房", platform="抖音",
        status="选题", related_property_id=prop.id, auto_generated=1,
    )
    db.add(c)
    _log(db, "选题生成", "豪宅公关", "自媒体内容",
         f"房源「{prop.name}」触发看房选题自动生成。")
    db.commit()
    return title


# ----------------------------------------------------------------------------
# 规则 3：区域情报聚合 → 调价 / 选题提示
# ----------------------------------------------------------------------------
DISTRICTS = ["福田", "南山", "宝中"]


def district_intelligence(db: Session) -> list:
    """聚合福田/南山/宝中的成交、在售、土拍数据，给出每个片区的情报卡。"""
    cards = []
    for d in DISTRICTS:
        txns = db.query(models.Transaction).filter(
            models.Transaction.district == d).all()
        props = db.query(models.Property).filter(
            models.Property.district == d, models.Property.status == "在售").all()
        auctions = db.query(models.LandAuction).filter(
            models.LandAuction.district == d).all()

        deal_count = len(txns)
        avg_deal = round(sum(t.deal_price or 0 for t in txns) / deal_count, 1) if deal_count else 0
        listing_unit = [p.unit_price for p in props if p.unit_price]
        avg_listing_unit = round(sum(listing_unit) / len(listing_unit)) if listing_unit else 0
        max_floor_price = max((a.floor_price or 0 for a in auctions), default=0)

        # 调价提示：若近期土拍楼面价 > 在售均价，说明面粉贵过面包 → 在售房源可挺价
        tip = ""
        if max_floor_price and avg_listing_unit and max_floor_price > avg_listing_unit:
            tip = (f"⚠️ {d}最新土拍楼面价({int(max_floor_price)})已超在售均价"
                   f"({avg_listing_unit})，面粉贵过面包，在售二手房源建议挺价/上调报价。")
        elif deal_count >= 3:
            tip = f"{d}成交活跃（{deal_count}笔），可主推该片区做内容与带看。"

        cards.append({
            "district": d,
            "deal_count": deal_count,
            "avg_deal_price": avg_deal,
            "listing_count": len(props),
            "avg_listing_unit_price": avg_listing_unit,
            "max_floor_price": int(max_floor_price),
            "tip": tip,
        })
    return cards


# ----------------------------------------------------------------------------
# 规则 4：VIP 会面 brief 自动生成
# ----------------------------------------------------------------------------
def build_meeting_brief(db: Session, client_id: int) -> str:
    """拉取客户全板块画像，生成一页纸会面 brief。"""
    client = db.query(models.Client).get(client_id)
    if not client:
        return ""

    txns = db.query(models.Transaction).filter(
        models.Transaction.client_id == client_id).all()
    total_deal = sum(t.deal_price or 0 for t in txns)
    needs = client.needs or {}
    open_needs = [k for k, v in needs.items() if not v]   # 未满足需求 = 机会点
    met_needs = [k for k, v in needs.items() if v]

    lines = [
        f"客户会面 Brief —— {client.name}（{client.level}，价值分 {client.value_score}）",
        f"联系方式：{client.phone or '-'}　来源：{client.source or '-'}",
        f"预估净资产：{int(client.net_worth_estimate or 0)} 万　兴趣片区：{'、'.join(client.interest_districts or []) or '-'}",
        "-" * 40,
        f"成交历史：{len(txns)} 笔，累计 {int(total_deal)} 万",
    ]
    for t in txns:
        lines.append(f"  · {t.deal_type} {t.district or ''} 成交 {int(t.deal_price)}万（佣金{t.commission}万）")
    lines.append("-" * 40)
    lines.append(f"已配置：{'、'.join(met_needs) or '无'}")
    lines.append(f"机会点（建议本次切入）：{'、'.join(open_needs) or '无'}")

    # 跨板块推荐话术
    recs = recommend_cross_module(db, client)
    if recs:
        lines.append("-" * 40)
        lines.append("协同切入建议：")
        for r in recs:
            lines.append(f"  → {r}")

    brief = "\n".join(lines)
    _log(db, "会面brief生成", "客户会面", "全板块",
         f"为客户「{client.name}」生成会面 brief。", ref_client_id=client.id)
    return brief


# ----------------------------------------------------------------------------
# 跨板块推荐：给定客户，推荐他可能需要的其它板块服务
# ----------------------------------------------------------------------------
def recommend_cross_module(db: Session, client: models.Client) -> list:
    recs = []
    needs = client.needs or {}
    txns = db.query(models.Transaction).filter(
        models.Transaction.client_id == client.id).all()
    total_deal = sum(t.deal_price or 0 for t in txns)

    if total_deal >= 1500 and not needs.get("理财"):
        recs.append("大额购房客户，资金充裕 → 推荐理财产品配置咨询。")
    if total_deal >= 2000 and not needs.get("香港身份"):
        recs.append("高资产客户 → 可切入香港身份规划（资产全球化配置）。")
    if not needs.get("保险"):
        recs.append("家庭资产保全 → 推荐大额保单/保险配置。")
    if not needs.get("子女教育") and (client.net_worth_estimate or 0) >= 3000:
        recs.append("高净值家庭 → 子女教育规划（学区+海外教育）切入。")
    if client.level == "VIP" and "豪宅意向" not in (client.tags or []):
        recs.append("VIP 客户 → 邀约最新豪宅看房，置换升级。")
    return recs


# ----------------------------------------------------------------------------
# 工具：写协同事件日志
# ----------------------------------------------------------------------------
def _log(db, event_type, source, target, desc, ref_client_id=None):
    db.add(models.SynergyEvent(
        event_type=event_type, source_module=source, target_module=target,
        description=desc, ref_client_id=ref_client_id, created_at=datetime.utcnow(),
    ))


# ----------------------------------------------------------------------------
# LLM 增强接口（可选，默认走规则；接入大模型时实现此函数即可）
# ----------------------------------------------------------------------------
def generate_topic_with_llm(context: str) -> str:
    """预留：用 LLM 把区域情报/土拍数据生成更有网感的爆款选题。"""
    raise NotImplementedError("接入 LLM 后实现：输入 context，返回选题标题")
