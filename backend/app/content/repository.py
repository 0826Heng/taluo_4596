from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class TarotCard:
    card_id: str
    meaning_upright: str
    meaning_reversed: str


@dataclass(frozen=True)
class TarotSpread:
    spread_id: str
    positions: list[str]  # 每个位置的 key，用于前端展示


@dataclass(frozen=True)
class SelectedContentVersions:
    tarotCardsVersion: str
    spreadsVersion: str
    contentVersion: str  # combined id，写入 session 便于追溯
    updatedAt: str


def _versions_dir() -> str:
    # backend/app/content/versions/
    return os.path.join(os.path.dirname(__file__), "versions")


def _manifest_path() -> str:
    return os.path.join(_versions_dir(), "manifest.json")


_MANIFEST_CACHE: Optional[Dict[str, Any]] = None
_MANIFEST_MTIME: Optional[float] = None


def _load_manifest() -> dict[str, Any]:
    global _MANIFEST_CACHE, _MANIFEST_MTIME
    path = _manifest_path()
    mtime = os.path.getmtime(path)
    if _MANIFEST_CACHE is not None and _MANIFEST_MTIME == mtime:
        return _MANIFEST_CACHE

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _MANIFEST_CACHE = data
    _MANIFEST_MTIME = mtime
    return data


def _load_json_list(filename: str) -> list[dict[str, Any]]:
    path = os.path.join(_versions_dir(), filename)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _hash_to_unit_interval(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    # 取前 16 hex = 64bit
    n = int(digest[:16], 16)
    return n / float(2**64)


def _select_by_gray(
    *,
    seed: str,
    active_version: str,
    gray_candidates: list[dict[str, Any]],
) -> str:
    # gray_candidates: [{"version": "...", "weight": 0.1}, ...]
    gray_candidates = [c for c in gray_candidates if (c.get("weight") or 0) > 0 and c.get("version")]
    if not gray_candidates:
        return active_version

    total = sum(float(c["weight"]) for c in gray_candidates)
    if total <= 0:
        return active_version

    u = _hash_to_unit_interval(seed)  # [0,1)
    if u >= total:
        return active_version

    # 归一化到候选总权重上分配
    remaining = u * total
    for c in gray_candidates:
        w = float(c["weight"])
        if remaining < w:
            return str(c["version"])
        remaining -= w

    return active_version


def select_content_versions(*, user_id: str, date_key: str) -> SelectedContentVersions:
    manifest = _load_manifest()
    updated_at = manifest.get("updatedAt") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    active_tarot_cards = manifest["active"]["tarotCards"]
    active_spreads = manifest["active"]["spreads"]

    gray_cfg = manifest.get("gray") or {}
    gray_enabled = bool(gray_cfg.get("enabled"))

    cards_gray = gray_cfg.get("tarotCards") or []
    spreads_gray = gray_cfg.get("spreads") or []

    base_seed = f"{user_id}|{date_key}"

    if gray_enabled:
        tarot_cards_version = _select_by_gray(
            seed=base_seed + "|cards",
            active_version=active_tarot_cards,
            gray_candidates=cards_gray,
        )
        spreads_version = _select_by_gray(
            seed=base_seed + "|spreads",
            active_version=active_spreads,
            gray_candidates=spreads_gray,
        )
    else:
        tarot_cards_version = active_tarot_cards
        spreads_version = active_spreads

    content_version = f"cards_{tarot_cards_version}|spreads_{spreads_version}"
    return SelectedContentVersions(
        tarotCardsVersion=tarot_cards_version,
        spreadsVersion=spreads_version,
        contentVersion=content_version,
        updatedAt=updated_at,
    )


def get_active_content_versions() -> SelectedContentVersions:
    manifest = _load_manifest()
    updated_at = manifest.get("updatedAt") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    active_tarot_cards = manifest["active"]["tarotCards"]
    active_spreads = manifest["active"]["spreads"]
    return SelectedContentVersions(
        tarotCardsVersion=active_tarot_cards,
        spreadsVersion=active_spreads,
        contentVersion=f"cards_{active_tarot_cards}|spreads_{active_spreads}",
        updatedAt=updated_at,
    )


def _parse_cards(rows: Iterable[dict[str, Any]]) -> list[TarotCard]:
    out: list[TarotCard] = []
    for r in rows:
        out.append(
            TarotCard(
                card_id=str(r.get("card_id")),
                meaning_upright=str(r.get("meaning_upright") or ""),
                meaning_reversed=str(r.get("meaning_reversed") or ""),
            )
        )
    return out


def _parse_spreads(rows: Iterable[dict[str, Any]]) -> list[TarotSpread]:
    out: list[TarotSpread] = []
    for r in rows:
        out.append(
            TarotSpread(
                spread_id=str(r.get("spread_id")),
                positions=[str(x) for x in (r.get("positions") or [])],
            )
        )
    return out


def load_tarot_cards(*, tarot_cards_version: str) -> list[TarotCard]:
    rows = _load_json_list(f"tarot_cards_{tarot_cards_version}.json")
    cards = _parse_cards(rows)
    if not cards:
        raise ValueError("empty_tarot_cards")
    return cards


def load_spreads(*, spreads_version: str) -> list[TarotSpread]:
    rows = _load_json_list(f"spreads_{spreads_version}.json")
    spreads = _parse_spreads(rows)
    if not spreads:
        raise ValueError("empty_spreads")
    return spreads


def resolve_spread(*, spread_id: str, spreads_version: str) -> TarotSpread:
    spreads = load_spreads(spreads_version=spreads_version)
    for s in spreads:
        if s.spread_id == spread_id:
            return s
    # 回退：三张阵
    for s in spreads:
        if s.spread_id == "spread_three_cards":
            return s
    return spreads[0]


def get_spreads(*, spreads_version: str) -> list[TarotSpread]:
    return load_spreads(spreads_version=spreads_version)


def draw_cards_for_spread(
    *,
    spread: TarotSpread,
    seed: str,
    tarot_cards_version: str,
) -> list[dict[str, Any]]:
    """
    抽牌逻辑（开发期）：seed 保证幂等；正逆位用均匀概率。
    后续可替换为“牌组抽取 + 逆位概率 + 约束”。
    """
    rng = random.Random(seed)
    cards = load_tarot_cards(tarot_cards_version=tarot_cards_version)
    out: list[dict[str, Any]] = []
    for pos_key in spread.positions:
        card = rng.choice(cards)
        upright = rng.random() >= 0.5
        meaning = card.meaning_upright if upright else card.meaning_reversed
        out.append(
            {
                "positionKey": pos_key,
                "cardId": card.card_id,
                "upright": upright,
                "interpretation": meaning,
            }
        )
    return out


def today_date_key(date: Optional[str] = None) -> str:
    if date:
        return date
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

