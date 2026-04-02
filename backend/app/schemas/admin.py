from __future__ import annotations

from pydantic import BaseModel


class ContentVersionResponse(BaseModel):
    tarotCardsVersion: str
    spreadsVersion: str
    updatedAt: str

