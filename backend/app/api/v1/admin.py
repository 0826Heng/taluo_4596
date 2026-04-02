from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from backend.app.content.repository import get_active_content_versions
from backend.app.core.auth import require_admin_secret
from backend.app.schemas.admin import ContentVersionResponse

router = APIRouter()


@router.get("/v1/admin/content/version", response_model=ContentVersionResponse)
async def get_content_version(_: Any = Depends(require_admin_secret)) -> ContentVersionResponse:
    v = get_active_content_versions()
    return ContentVersionResponse(
        tarotCardsVersion=v.tarotCardsVersion,
        spreadsVersion=v.spreadsVersion,
        updatedAt=v.updatedAt or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

