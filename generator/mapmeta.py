#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从已生成的地图 HTML 中抽取卡片所需的元信息（中文标题/emoji/标签/配色/图片搜索词）。
供 build_static.py 与 server.py 共用，让 Hub 画廊卡片用真实标题而非 slug 猜测。"""
import json
import re

_META_RE = re.compile(r"const META = (\{.*?\});", re.S)
_EMOJI_PREFIX = re.compile(r"^[\U0001F000-\U0001FAFF☀-➿️\s]+")
_LEGEND_ITEM_RE = re.compile(
    r'class="legend-dot"[^>]*>(.*?)</span>\s*([^<]+?)\s*</div>', re.S
)


def _legend_tags(html, limit=4):
    tags = []
    for icon, label in _LEGEND_ITEM_RE.findall(html):
        icon, label = icon.strip(), label.strip()
        if label:
            tags.append(f"{icon} {label}".strip())
        if len(tags) >= limit:
            break
    return tags


def _clean_title(meta):
    t = (meta.get("title_short") or meta.get("title") or "").strip()
    return _EMOJI_PREFIX.sub("", t).strip()


def _image_query(meta):
    """优先用 eyebrow 的首段（多为地名，如 ALASKA / KYOTO / BARCELONA），
    否则取 subtitle 里最像英文地名的一段。"""
    eb = (meta.get("eyebrow") or "").split("·")[0].strip()
    if eb and re.search(r"[A-Za-z]", eb) and not re.search(r"livemap|\d{4}", eb, re.I):
        return eb
    for seg in re.split(r"[·•・|]", meta.get("subtitle") or ""):
        seg = seg.strip()
        if seg and re.search(r"[A-Za-z]", seg) and not re.search(r"livemap|\d{4}", seg, re.I):
            return seg
    return _clean_title(meta)


def card_meta(html_path):
    """返回 {title, emoji, en, query, color_scheme, tags}，解析失败时返回 {}。"""
    try:
        html = html_path.read_text(encoding="utf-8")
        m = _META_RE.search(html)
        if not m:
            return {}
        meta = json.loads(m.group(1))
        tags = _legend_tags(html)
        en = (meta.get("eyebrow") or "").split("·")[0].strip() or _image_query(meta)
        return {
            "title": _clean_title(meta),
            "emoji": (meta.get("header_emoji") or "").strip(),
            "en": en.upper(),
            "query": _image_query(meta),
            "color_scheme": meta.get("color_scheme") or "",
            "tags": tags,
        }
    except Exception:
        return {}
