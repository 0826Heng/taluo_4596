from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Tuple


_lock = threading.Lock()


def _data_dir() -> str:
    # backend/app/storage -> backend/data
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))


def _history_path() -> str:
    return os.path.join(_data_dir(), "tarot_history.jsonl")


def _ensure_data_dir() -> None:
    os.makedirs(_data_dir(), exist_ok=True)


def _utc_iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


@dataclass(frozen=True)
class HistoryItem:
    session_id: str
    created_at: str
    theme_id: str
    spread_id: str
    reflection_summary: str
    tags: list[str]


class HistoryStore:
    """
    轻量级文件存储（仅用于项目骨架/开发期）。
    真实上线请替换为 MySQL/PostgreSQL + 事务。
    """

    def __init__(self) -> None:
        _ensure_data_dir()

    def upsert_session_draw(
        self,
        *,
        user_id: str,
        session_id: str,
        theme_id: str,
        spread_id: str,
        content_version: str,
        draw_result: list[dict[str, Any]],
        date_key: str,
        seed: str,
        created_at: float,
    ) -> None:
        record = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": _utc_iso(created_at),
            "theme_id": theme_id,
            "spread_id": spread_id,
            "content_version": content_version,
            "draw_result": draw_result,
            "date_key": date_key,
            "seed": seed,
            "reflection_text": None,
            "reflection_summary": "",
            "tags": [],
        }
        with _lock:
            self._upsert_by_session_id(record)

    def add_reflection(
        self,
        *,
        user_id: str,
        session_id: str,
        reflection_text: str,
        tags: Optional[list[str]],
        reflection_summary: str,
    ) -> None:
        with _lock:
            self._ensure_loaded_and_upsert(
                user_id=user_id,
                session_id=session_id,
                reflection_text=reflection_text,
                reflection_summary=reflection_summary,
                tags=tags or [],
            )

    def list_history(
        self, *, user_id: str, cursor: int, limit: int = 20
    ) -> Tuple[list[HistoryItem], Optional[int]]:
        # cursor：偏移量（开发期简化）
        items: list[HistoryItem] = []
        with _lock:
            for rec in self._iter_all_records():
                if rec.get("user_id") != user_id:
                    continue
                created_at = rec.get("created_at") or ""
                theme_id = rec.get("theme_id") or ""
                spread_id = rec.get("spread_id") or ""
                reflection_summary = rec.get("reflection_summary") or ""
                tags = rec.get("tags") or []
                items.append(
                    HistoryItem(
                        session_id=rec.get("session_id") or "",
                        created_at=created_at,
                        theme_id=theme_id,
                        spread_id=spread_id,
                        reflection_summary=reflection_summary,
                        tags=tags,
                    )
                )

        # 按 created_at 近似排序（此处按文件读取顺序；真实 DB 需 ORDER BY）
        page = items[cursor : cursor + limit]
        next_cursor = cursor + limit if cursor + limit < len(items) else None
        return page, next_cursor

    def _iter_all_records(self) -> Iterable[dict[str, Any]]:
        path = _history_path()
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)

    def _upsert_by_session_id(self, record: dict[str, Any]) -> None:
        path = _history_path()
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return

        # 读全量再写（骨架用途）
        all_records = list(self._iter_all_records())
        updated = False
        for i, rec in enumerate(all_records):
            if rec.get("user_id") == record.get("user_id") and rec.get(
                "session_id"
            ) == record.get("session_id"):
                all_records[i] = record
                updated = True
                break

        if not updated:
            all_records.append(record)

        with open(path, "w", encoding="utf-8") as f:
            for rec in all_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def _ensure_loaded_and_upsert(
        self,
        *,
        user_id: str,
        session_id: str,
        reflection_text: str,
        reflection_summary: str,
        tags: list[str],
    ) -> None:
        path = _history_path()
        all_records = list(self._iter_all_records())
        found = False
        for i, rec in enumerate(all_records):
            if rec.get("user_id") == user_id and rec.get("session_id") == session_id:
                rec["reflection_text"] = reflection_text
                rec["reflection_summary"] = reflection_summary
                rec["tags"] = tags
                all_records[i] = rec
                found = True
                break
        if not found:
            # 如果没找到 session，仍然写一条最小记录（开发期容错）
            all_records.append(
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "created_at": _utc_iso(time.time()),
                    "theme_id": "",
                    "spread_id": "",
                    "content_version": "",
                    "draw_result": [],
                    "date_key": "",
                    "seed": "",
                    "reflection_text": reflection_text,
                    "reflection_summary": reflection_summary,
                    "tags": tags,
                }
            )

        with open(path, "w", encoding="utf-8") as f:
            for rec in all_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

