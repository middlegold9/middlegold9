"""路由注册聚合。"""
from . import (
    clients, properties, transactions, land_auction,
    content, meetings, contracts, synergy, ingestion_api,
)

all_routers = [
    clients.router,
    properties.router,
    transactions.router,
    land_auction.router,
    content.router,
    meetings.router,
    contracts.router,
    synergy.router,
    ingestion_api.router,
]
