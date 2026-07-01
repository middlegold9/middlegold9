"""Pydantic 数据校验模型（API 出入参）。"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ClientBase(BaseModel):
    name: str
    phone: Optional[str] = None
    level: str = "普通"
    source: Optional[str] = None
    net_worth_estimate: float = 0
    needs: Dict[str, Any] = {}
    tags: List[str] = []
    interest_districts: List[str] = []
    note: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientOut(ClientBase):
    id: int
    value_score: float = 0
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyBase(BaseModel):
    name: str
    district: Optional[str] = None
    block: Optional[str] = None
    category: Optional[str] = None
    area: Optional[float] = None
    total_price: Optional[float] = None
    unit_price: Optional[float] = None
    status: str = "在售"
    selling_points: List[str] = []
    source_doc: Optional[str] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyOut(PropertyBase):
    id: int

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    client_id: Optional[int] = None
    property_id: Optional[int] = None
    deal_type: str = "二手"
    deal_price: float = 0
    commission: float = 0
    district: Optional[str] = None
    source_doc: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionOut(TransactionBase):
    id: int
    deal_date: datetime

    class Config:
        from_attributes = True


class LandAuctionBase(BaseModel):
    parcel_no: Optional[str] = None
    district: Optional[str] = None
    location: Optional[str] = None
    floor_price: Optional[float] = None
    premium_rate: Optional[float] = None
    winner: Optional[str] = None
    note: Optional[str] = None
    source_doc: Optional[str] = None


class LandAuctionCreate(LandAuctionBase):
    pass


class LandAuctionOut(LandAuctionBase):
    id: int
    auction_date: datetime

    class Config:
        from_attributes = True


class ContentBase(BaseModel):
    title: str
    category: Optional[str] = None
    platform: Optional[str] = None
    status: str = "选题"
    related_property_id: Optional[int] = None
    related_auction_id: Optional[int] = None
    leads_count: int = 0


class ContentCreate(ContentBase):
    pass


class ContentOut(ContentBase):
    id: int
    auto_generated: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class MeetingBase(BaseModel):
    client_id: int
    meet_date: Optional[datetime] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    status: str = "待确认"


class MeetingCreate(MeetingBase):
    pass


class MeetingOut(MeetingBase):
    id: int
    brief: Optional[str] = None

    class Config:
        from_attributes = True


class ContractOut(BaseModel):
    id: int
    transaction_id: Optional[int] = None
    client_id: Optional[int] = None
    contract_type: Optional[str] = None
    content: Optional[str] = None
    status: str = "草稿"
    created_at: datetime

    class Config:
        from_attributes = True


class SynergyEventOut(BaseModel):
    id: int
    event_type: str
    source_module: Optional[str] = None
    target_module: Optional[str] = None
    description: Optional[str] = None
    ref_client_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Client360(BaseModel):
    """客户 360 视图：把一个客户在所有板块的足迹聚合。"""
    client: ClientOut
    transactions: List[TransactionOut] = []
    meetings: List[MeetingOut] = []
    contracts: List[ContractOut] = []
    recommendations: List[str] = []
