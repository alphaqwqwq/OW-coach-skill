"""从 Fandom wiki 抓取英雄策略文本和职责细分数据。
使用 Fandom API (parse action)，缓存到本地避免重复请求。

策略文本获取方式（优先级递减）：
  1. 全页 HTML → 以 "Strategy" 标题为锚点裁剪策略相关内容
  2. 按角色尝试不同章节名（输出/重装/支援）
  3. 按章节名列表逐一尝试

API: https://overwatch.fandom.com/api.php
"""

import html as html_mod
import json
import os
import re
from functools import lru_cache
from urllib.parse import unquote

import requests

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fandom_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

API_BASE = "https://overwatch.fandom.com/api.php"
HEADERS = {"User-Agent": "OW-Coach/1.0"}

# overlab ID → Fandom 页面名映射
PAGE_MAP = {
    # 重装
    "domina": "Domina",
    "reinhardt": "Reinhardt", "ramattra": "Ramattra", "sigma": "Sigma",
    "orisa": "Orisa", "roadhog": "Roadhog", "mauga": "Mauga",
    "junker-queen": "Junker_Queen", "zarya": "Zarya",
    "dva": "D.Va", "winston": "Winston", "wrecking-ball": "Wrecking_Ball",
    "doomfist": "Doomfist", "hazard": "Hazard",
    # 输出
    "tracer": "Tracer", "reaper": "Reaper", "genji": "Genji",
    "pharah": "Pharah", "sombra": "Sombra", "echo": "Echo",
    "mei": "Mei", "bastion": "Bastion", "hanzo": "Hanzo",
    "widowmaker": "Widowmaker", "junkrat": "Junkrat",
    "torbjorn": "Torbj%C3%B6rn", "symmetra": "Symmetra",
    "ashe": "Ashe", "cassidy": "Cassidy", "sojourn": "Sojourn",
    "venture": "Venture", "freja": "Freja",
    "soldier-76": "Soldier:_76", "emre": "Emre",
    "vendetta": "Vendetta", "sierra": "Sierra",
    "anran": "Anran", "shion": "Shion",
    # 支援
    "ana": "Ana", "mercy": "Mercy", "zenyatta": "Zenyatta",
    "lucio": "L%C3%BAcio", "moira": "Moira", "brigitte": "Brigitte",
    "baptiste": "Baptiste", "lifeweaver": "Lifeweaver",
    "kiriko": "Kiriko", "illari": "Illari", "juno": "Juno",
    "wuyang": "Wuyang", "mizuki": "Mizuki",
    "jetpack-cat": "Jetpack_Cat",
}

# 英雄职责映射（用于角色相关的章节回退策略）
ROLE_MAP: dict[str, str] = {
    # 重装
    "domina": "tank", "reinhardt": "tank", "ramattra": "tank",
    "sigma": "tank", "orisa": "tank", "roadhog": "tank",
    "mauga": "tank", "junker-queen": "tank", "zarya": "tank",
    "dva": "tank", "winston": "tank", "wrecking-ball": "tank",
    "doomfist": "tank", "hazard": "tank",
    # 输出
    "tracer": "damage", "reaper": "damage", "genji": "damage",
    "pharah": "damage", "sombra": "damage", "echo": "damage",
    "mei": "damage", "bastion": "damage", "hanzo": "damage",
    "widowmaker": "damage", "junkrat": "damage",
    "torbjorn": "damage", "symmetra": "damage",
    "ashe": "damage", "cassidy": "damage", "sojourn": "damage",
    "venture": "damage", "freja": "damage",
    "soldier-76": "damage", "emre": "damage",
    "vendetta": "damage", "sierra": "damage",
    "anran": "damage", "shion": "damage",
    # 支援
    "ana": "support", "mercy": "support", "zenyatta": "support",
    "lucio": "support", "moira": "support", "brigitte": "support",
    "baptiste": "support", "lifeweaver": "support",
    "kiriko": "support", "illari": "support", "juno": "support",
    "wuyang": "support", "mizuki": "support",
    "jetpack-cat": "support",
}


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _resolve_page_name(fandom_page: str) -> str:
    """URL 解码页面名（如 L%C3%BAcio → Lúcio），Fandom API 不接受 URL 编码。"""
    return unquote(fandom_page)


def _api(action: str, **params) -> dict:
    """调用 Fandom API。自动确保 page 参数已解码。"""
    if "page" in params:
        params["page"] = _resolve_page_name(params["page"])
    params["action"] = action
    params["format"] = "json"
    resp = requests.get(API_BASE, params=params, headers=HEADERS, timeout=15)
    return resp.json()


def _clean_html(html_text: str) -> str:
    """去除 HTML 标签，合并空白。"""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


def _save_cache(cache_path: str, text: str, source: str) -> None:
    """保存缓存 JSON。"""
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({"text": text, "source": source}, f, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 章节列表相关
# ---------------------------------------------------------------------------

@lru_cache(maxsize=64)
def get_sections(fandom_page: str) -> list[dict]:
    """获取英雄页面的章节列表。返回 [{"index": str, "line": str}, ...]。"""
    data = _api("parse", page=fandom_page, prop="sections")
    return data.get("parse", {}).get("sections", [])


def find_section_index(fandom_page: str, target: str) -> str | None:
    """在章节列表中查找指定标题的 index。
    自动处理 API 返回的 HTML entity（&amp; → &）。
    """
    decoded_target = html_mod.unescape(target)
    for s in get_sections(fandom_page):
        line = html_mod.unescape(s["line"])
        if line == decoded_target:
            return s["index"]
    return None


# ---------------------------------------------------------------------------
# 策略文本获取（主逻辑）
# ---------------------------------------------------------------------------

def _fetch_section_text(fandom_page: str, section_index: str) -> str | None:
    """获取单个章节的纯文本内容（已清理 HTML）。"""
    data = _api("parse", page=fandom_page, prop="text", section=section_index)
    html = data.get("parse", {}).get("text", {}).get("*", "")
    if not html:
        return None
    return _clean_html(html)


def _extract_strategy_from_full_html(html_text: str) -> str | None:
    """从全页 HTML 中裁剪 Strategy 章节内容。
    
    查找 <h2> 中 id="Strategy" 的标题，提取其下直到下一个 <h2> 的所有内容。
    """
    # 匹配 Strategy h2 标题到下一个 h2 之间的所有内容
    pattern = re.compile(
        r'<h2[^>]*>\s*<span[^>]*id="Strategy"[^>]*>.*?</h2>\s*'
        r'(.*?)'
        r'(?=<h2[^>]*>|$)',
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(html_text)
    if not match:
        return None

    content_html = match.group(1)
    text = _clean_html(content_html)
    # 至少要有 50 个有意义的字符才认为有效
    if not text or len(text) < 50:
        return None
    return text


# 各职责的英雄，首选的章节名列表（按优先级递减）
_ROLE_SECTION_PREFERENCE: dict[str, list[str]] = {
    "damage":  ["Weapons & Abilities", "Strategy"],
    "tank":    ["Strategy", "Overview", "Abilities"],
    "support": ["Strategy", "Abilities"],
}

# 通用章节回退列表（全角色）
_FALLBACK_SECTIONS = [
    "Strategy",
    "Weapons & Abilities",
    "General Strategies",
    "Overview",
    "Abilities",
]


def fetch_strategy(fandom_page: str) -> str | None:
    """从 Fandom 抓取完整的策略文本。
    
    获取方式（优先级递减）：
      1. 全页 HTML → 以 "Strategy" 标题锚点裁剪
      2. section 方式，按章节名逐项尝试
    
    缓存键 = {page}_strategy（不依赖章节号），避免索引变动导致缓存失效。
    """
    cache_key = f"{fandom_page}_strategy"
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")

    # ── 检查缓存 ──
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cached = json.load(f)
            return cached.get("text")

    # ── 方式一：全页 HTML 裁剪 ──
    data = _api("parse", page=fandom_page, prop="text")
    html_text = data.get("parse", {}).get("text", {}).get("*", "")
    if html_text:
        text = _extract_strategy_from_full_html(html_text)
        if text:
            _save_cache(cache_path, text, fandom_page)
            return text

    # ── 方式二：section 方式，尝试不同章节名 ──
    for target in _FALLBACK_SECTIONS:
        idx = find_section_index(fandom_page, target)
        if idx:
            text = _fetch_section_text(fandom_page, idx)
            if text:
                _save_cache(cache_path, text, fandom_page)
                return text

    return None


# ---------------------------------------------------------------------------
# 公共 API
# ---------------------------------------------------------------------------

def get_hero_strategy(overlab_id: str) -> str | None:
    """获取英雄的策略文本（供 agent 注入提示词）。

    Args:
        overlab_id: overlab.cn 的英雄 ID（如 "ana", "tracer"）。
    """
    page = PAGE_MAP.get(overlab_id)
    if not page:
        return None
    return fetch_strategy(page)


def _extract_overview_section(fandom_page: str) -> str | None:
    """从 Overview 章节提取英雄定位描述（简洁版）。"""
    idx = find_section_index(fandom_page, "Overview")
    if not idx:
        return None

    html_text = _fetch_section_text(fandom_page, idx)
    if not html_text:
        return None

    # 取第一句
    sentences = html_text.split(". ")
    if sentences:
        return sentences[0].strip() + "."
    return html_text[:200] + "..."


def get_hero_overview(overlab_id: str) -> str | None:
    """获取英雄的简短定位描述。"""
    page = PAGE_MAP.get(overlab_id)
    if not page:
        return None
    return _extract_overview_section(page)


# ---------------------------------------------------------------------------
# 批量预处理
# ---------------------------------------------------------------------------

def warm_cache_for_all() -> dict[str, str | None]:
    """遍历 PAGE_MAP 中所有英雄，预热策略文本缓存。
    返回 {overlab_id: strategy_text_or_None}。
    """
    results: dict[str, str | None] = {}
    total = len(PAGE_MAP)
    print(f"Warming fandom cache for {total} heroes...")

    for i, (hid, page) in enumerate(PAGE_MAP.items(), 1):
        try:
            text = get_hero_strategy(hid)
            status = "OK" if text else "EMPTY"
            length = len(text) if text else 0
            print(f"  [{i:2d}/{total}] {hid:20s} -> {page:20s}  {status} ({length} chars)")
        except Exception as e:
            print(f"  [{i:2d}/{total}] {hid:20s} -> ERROR: {e}")
            text = None
        results[hid] = text

    success = sum(1 for v in results.values() if v)
    print(f"\nDone. {success}/{total} heroes cached successfully.")
    return results


if __name__ == "__main__":
    # 直接运行本文件即可预热缓存
    warm_cache_for_all()
