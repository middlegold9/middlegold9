"""FastAPI 入口 —— 深圳房产博主一体化工作流系统。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import all_routers

app = FastAPI(
    title="深圳房产博主一体化工作流系统",
    description="FDE 项目：统一数据底座 + 跨板块协同引擎，解决数据散落与板块孤岛问题。",
    version="1.0.0",
)

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"msg": "深圳房产 FDE 工作流系统 API 运行中，访问 /docs 查看接口文档。"}


for r in all_routers:
    app.include_router(r)
