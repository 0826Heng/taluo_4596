from __future__ import annotations

import hashlib
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.app.content.repository import (
    draw_cards_for_spread,
    get_active_content_versions,
    get_spreads,
    resolve_spread,
    select_content_versions,
    today_date_key,
)
from backend.app.core.auth import require_user_id
from backend.app.core.content_safety import assert_text_is_safe
from backend.app.core.rate_limiter import check_rate_limit
from backend.app.schemas.tarot import (
    ListHistoryResponse,
    SaveReflectionRequest,
    TodayRequest,
    TodayResponse,
    TarotReadingRequest,
    TarotReadingResponse,
)
from backend.app.storage.history_store import HistoryStore

router = APIRouter()

_THEME_IDS = ["theme_relationship", "theme_career", "theme_learning", "theme_growth"]

store = HistoryStore()


def _safe_reflection_summary(text: str) -> str:
    # 开发期：用截断生成摘要；正式可接入“无敏感扩写”的摘要策略。
    t = (text or "").strip().replace("\n", " ").replace("\r", " ")
    if not t:
        return ""
    return t[:80]


def _make_seed(user_id: str, spread_id: str, theme_id: str, client_nonce: str) -> str:
    raw = f"{user_id}|{spread_id}|{theme_id}|{client_nonce}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.post("/v1/tarot/reading", response_model=TarotReadingResponse)
async def create_reading(
    payload: TarotReadingRequest,
    request: Request,
    user_id: str = Depends(require_user_id),
) -> TarotReadingResponse:
    check_rate_limit(user_id=user_id, path="tarot.reading")

    theme_id = payload.themeId
    spread_id = payload.spreadId
    positions = payload.positions
    client_nonce = payload.clientNonce

    # 基本校验：避免空串和明显异常
    if not theme_id or not spread_id:
        raise HTTPException(status_code=400, detail="invalid_theme_or_spread")

    date_key = today_date_key()
    selected_versions = select_content_versions(user_id=user_id, date_key=date_key)

    spread = resolve_spread(spread_id=spread_id, spreads_version=selected_versions.spreadsVersion)
    if positions and len(positions) == len(spread.positions):
        # 若前端提供了 positions，则覆盖位置 key（仅用于展示）
        spread = type(spread)(
            spread_id=spread.spread_id,
            positions=positions,
        )

    seed = _make_seed(user_id, spread_id, theme_id, client_nonce)
    session_id = f"{user_id}-{client_nonce}"

    draw_result = draw_cards_for_spread(
        spread=spread,
        seed=seed,
        tarot_cards_version=selected_versions.tarotCardsVersion,
    )

    # 生成文本安全校验（二次防护）
    for item in draw_result:
        assert_text_is_safe(item.get("interpretation") or "", allow_empty=False)

    store.upsert_session_draw(
        user_id=user_id,
        session_id=session_id,
        theme_id=theme_id,
        spread_id=spread_id,
        content_version=selected_versions.contentVersion,
        draw_result=draw_result,
        date_key=date_key,
        seed=seed,
        created_at=time.time(),
    )

    return TarotReadingResponse(
        drawResult=draw_result,
        sessionId=session_id,
        contentVersion=selected_versions.contentVersion,
    )


@router.post("/v1/tarot/history")
async def save_history(
    payload: SaveReflectionRequest,
    request: Request,
    user_id: str = Depends(require_user_id),
) -> dict[str, Any]:
    check_rate_limit(user_id=user_id, path="tarot.history.save")

    if not payload.sessionId:
        raise HTTPException(status_code=400, detail="missing_session_id")

    reflection_text = (payload.reflectionText or "").strip()
    # 反向保护：如果前端传入了不安全内容，直接拒绝
    assert_text_is_safe(reflection_text, allow_empty=False)

    summary = _safe_reflection_summary(reflection_text)
    if summary:
        assert_text_is_safe(summary, allow_empty=False)

    store.add_reflection(
        user_id=user_id,
        session_id=payload.sessionId,
        reflection_text=reflection_text,
        reflection_summary=summary,
        tags=payload.tags or [],
    )

    return {"ok": True}


@router.get("/v1/tarot/history", response_model=ListHistoryResponse)
async def list_history(
    cursor: int = Query(default=0, ge=0),
    user_id: str = Depends(require_user_id),
) -> ListHistoryResponse:
    check_rate_limit(user_id=user_id, path="tarot.history.list")

    items, next_cursor = store.list_history(user_id=user_id, cursor=cursor)
    return ListHistoryResponse(
        items=[
            {
                "sessionId": i.session_id,
                "createdAt": i.created_at,
                "themeId": i.theme_id,
                "spreadId": i.spread_id,
                "reflectionSummary": i.reflection_summary,
            }
            for i in items
        ],
        nextCursor=next_cursor,
    )


@router.post("/v1/tarot/today", response_model=TodayResponse)
async def get_today(
    payload: TodayRequest,
    user_id: str = Depends(require_user_id),
) -> TodayResponse:
    # 今日主题/牌阵建议：开发期用确定性映射（避免请求结果随时间抖动）
    _ = user_id  # 当前未做“偏好归因”，仅保留鉴权占位

    date_key = today_date_key(payload.date)

    # 基于 date_key 做稳定选择
    idx = int(hashlib.sha256(date_key.encode("utf-8")).hexdigest(), 16) % len(_THEME_IDS)
    theme_id = _THEME_IDS[idx]

    active = get_active_content_versions()
    spreads = get_spreads(spreads_version=active.spreadsVersion)
    spread_id = spreads[0].spread_id if not spreads else spreads[idx % len(spreads)].spread_id

    return TodayResponse(dateKey=date_key, themeId=theme_id, spreadId=spread_id)

