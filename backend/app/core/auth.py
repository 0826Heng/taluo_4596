from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, Request

from backend.app.core.config import settings


async def require_user_id(request: Request) -> str:
    user_id = request.headers.get(settings.openid_header)
    if not user_id:
        raise HTTPException(status_code=401, detail="missing_user_id")
    return user_id


async def require_admin_secret(x_admin_secret: Optional[str] = Header(default=None)) -> None:
    if not settings.admin_secret:
        # 未配置时：拒绝管理接口
        raise HTTPException(status_code=404, detail="admin_unavailable")
    if not x_admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="invalid_admin_secret")

