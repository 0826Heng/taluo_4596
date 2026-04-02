from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.tarot import router as tarot_router

app = FastAPI(title="Tarot Symbolic Reading API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    # 为了本地“打开界面”不返回 404，提供一个简单入口提示。
    return {"message": "OK. Please open /docs or /health"}


app.include_router(tarot_router)
app.include_router(admin_router)

