from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DrawResultItem(BaseModel):
    positionKey: str
    cardId: str
    upright: bool
    interpretation: str


class TarotReadingRequest(BaseModel):
    spreadId: str
    themeId: str
    positions: Optional[list[str]] = None
    clientNonce: str
    lang: str = "zh"


class TarotReadingResponse(BaseModel):
    drawResult: list[DrawResultItem]
    sessionId: str
    contentVersion: str


class SaveReflectionRequest(BaseModel):
    sessionId: str
    reflectionText: str
    tags: Optional[list[str]] = None


class HistoryItem(BaseModel):
    sessionId: str
    createdAt: str
    themeId: str
    spreadId: str
    reflectionSummary: str


class ListHistoryResponse(BaseModel):
    items: list[HistoryItem]
    nextCursor: Optional[int] = None


class TodayRequest(BaseModel):
    date: Optional[str] = None
    themePreference: Optional[str] = None


class TodayResponse(BaseModel):
    dateKey: str
    themeId: str
    spreadId: str

