from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class SafetyMatch:
    phrase: str
    span: tuple[int, int]


# 仅用于“安全校验/拦截”，不要直接用于前端展示文本。
FORBIDDEN_VISIBLE_TERMS: List[str] = [
    "算命",
    "抽签",
    "星座运势",
    "预测未来",
    "包你一定",
    "必然发生",
    "封建迷信",
    "邪教",
    "迷信",
]

# 规则性“绝对化/恐吓/承诺”模式（可按审核反馈继续扩展）。
FORBIDDEN_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"一定会"),
    re.compile(r"必然"),
    re.compile(r"保证"),
    re.compile(r"不做就"),
    re.compile(r"否则就"),
]


def _iter_matches(text: str, phrases: Iterable[str]) -> Iterable[SafetyMatch]:
    for phrase in phrases:
        start = 0
        while True:
            idx = text.find(phrase, start)
            if idx < 0:
                break
            yield SafetyMatch(phrase=phrase, span=(idx, idx + len(phrase)))
            start = idx + len(phrase)


def contains_forbidden(text: str) -> List[SafetyMatch]:
    """
    检查文本是否包含高风险词/模式。
    返回匹配项列表；空表示未命中。
    """
    if not text:
        return []

    matches: List[SafetyMatch] = []
    matches.extend(list(_iter_matches(text, FORBIDDEN_VISIBLE_TERMS)))

    for pat in FORBIDDEN_PATTERNS:
        for m in pat.finditer(text):
            matches.append(SafetyMatch(phrase=pat.pattern, span=(m.start(), m.end())))

    return matches


def assert_text_is_safe(text: str, *, allow_empty: bool = False) -> None:
    """
    若命中高风险内容则抛出 ValueError（让上层决定返回什么错误码与提示文案）。
    """
    if (not text) and not allow_empty:
        raise ValueError("empty_text")

    hits = contains_forbidden(text)
    if hits:
        # 返回短信息给上层日志；避免把敏感内容原样回显给用户。
        hit_phrases = sorted({h.phrase for h in hits})
        raise ValueError(f"forbidden_content: {hit_phrases[:5]}")

