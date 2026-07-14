"""统一数据底座：把 7 大业务板块抽象为一张关系网。

设计原则：
  - Client（客户）是协同的中心节点，所有板块都指向它；
  - Property / LandAuction 是「区域情报」的两个数据来源；
  - Content / Lead 负责引流闭环；
  - Transaction / Contract / Meeting 是履约与服务动作。
"""
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Client(Base):
    """客户 / VIP —— 协同网络的中心节点。"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String)
    # 普通 / 高净值 / VIP
    level = Column(String, default="普通")
    source = Column(String)                       # 来源渠道：抖音/视频号/转介绍/老客户
    net_worth_estimate = Column(Float, default=0) # 预估净资产（万元）
    value_score = Column(Float, default=0)         # 协同引擎算出的客户价值分
    # 跨板块需求标签：{"理财": true, "保险": false, "香港身份": true, "子女教育": true}
    needs = Column(JSON, default=dict)
    tags = Column(JSON, default=list)              # ["豪宅意向", "宝中", "改善"]
    interest_districts = Column(JSON, default=list)  # ["福田", "南山", "宝中"]
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="client")
    meetings = relationship("Meeting", back_populates="client")
    contracts = relationship("Contract", back_populates="client")


class Property(Base):
    """房源 / 楼盘（新房、二手、豪宅）。"""
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    district = Column(String)               # 福田 / 南山 / 宝中
    block = Column(String)                  # 具体片区：香蜜湖/后海/宝中
    category = Column(String)               # 新房 / 二手 / 豪宅
    area = Column(Float)                    # 建筑面积 ㎡
    total_price = Column(Float)             # 总价（万元）
    unit_price = Column(Float)              # 单价（元/㎡）
    status = Column(String, default="在售")  # 在售 / 已成交 / 蓄客
    selling_points = Column(JSON, default=list)  # 卖点（供自媒体选题用）
    source_doc = Column(String)             # 数据来源文档
    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    """成交记录（二手 / 新房）。"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    property_id = Column(Integer, ForeignKey("properties.id"))
    deal_type = Column(String)              # 二手 / 新房
    deal_price = Column(Float)              # 成交价（万元）
    commission = Column(Float)              # 佣金（万元）
    deal_date = Column(DateTime, default=datetime.utcnow)
    district = Column(String)
    source_doc = Column(String)             # 来源 PDF/Word

    client = relationship("Client", back_populates="transactions")
    property = relationship("Property")


class LandAuction(Base):
    """土拍记录 —— 区域情报 + 自媒体选题的源头。"""
    __tablename__ = "land_auctions"

    id = Column(Integer, primary_key=True, index=True)
    parcel_no = Column(String)              # 地块编号
    district = Column(String)
    location = Column(String)
    floor_price = Column(Float)             # 楼面价（元/㎡）
    premium_rate = Column(Float)            # 溢价率 %
    winner = Column(String)                 # 竞得方
    auction_date = Column(DateTime, default=datetime.utcnow)
    note = Column(Text)
    source_doc = Column(String)


class Content(Base):
    """自媒体内容（豪宅看房 / 土拍分析）—— 引流闭环。"""
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String)               # 豪宅看房 / 土拍分析 / 区域解读
    platform = Column(String)               # 抖音 / 视频号 / 小红书
    status = Column(String, default="选题")  # 选题 / 拍摄中 / 已发布
    related_property_id = Column(Integer, ForeignKey("properties.id"))
    related_auction_id = Column(Integer, ForeignKey("land_auctions.id"))
    leads_count = Column(Integer, default=0)  # 引流线索数
    auto_generated = Column(Integer, default=0)  # 是否协同引擎自动生成
    created_at = Column(DateTime, default=datetime.utcnow)


class Lead(Base):
    """线索（来自内容引流）—— 待转化为 Client。"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    channel = Column(String)                # 抖音/视频号私信
    district_interest = Column(String)
    score = Column(Float, default=0)
    status = Column(String, default="待跟进")  # 待跟进 / 已转化 / 流失
    from_content_id = Column(Integer, ForeignKey("contents.id"))
    converted_client_id = Column(Integer, ForeignKey("clients.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Meeting(Base):
    """VIP 客户会面安排。"""
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    meet_date = Column(DateTime)
    location = Column(String)
    agenda = Column(String)                 # 议题：资产配置/看房/签约
    brief = Column(Text)                    # 协同引擎自动生成的会面 brief
    status = Column(String, default="待确认")  # 待确认 / 已确认 / 已完成

    client = relationship("Client", back_populates="meetings")


class Contract(Base):
    """合同（自动生成 + 人工校对）。"""
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    contract_type = Column(String)          # 二手买卖 / 居间服务 / 资产配置顾问
    content = Column(Text)                  # 合同正文
    status = Column(String, default="草稿")  # 草稿 / 待签 / 已签
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="contracts")


class SynergyEvent(Base):
    """协同事件日志 —— 记录引擎自动串联板块的每一个动作（可审计）。"""
    __tablename__ = "synergy_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)             # 客户升级/选题生成/调价提示/会面brief
    source_module = Column(String)          # 触发来源板块
    target_module = Column(String)          # 协同到的板块
    description = Column(Text)
    ref_client_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
