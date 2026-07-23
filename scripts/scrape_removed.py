"""从 overlab.cn 抓取英雄已移除内容（技能/威能变为基础技能等版本变动信息）。

用法:
    python scripts/scrape_removed.py              # 抓取所有英雄
    python scripts/scrape_removed.py reaper       # 仅抓取指定英雄
    python scripts/scrape_removed.py ana baptiste # 抓取多个英雄

作为模块导入:
    from scrape_removed import scrape_hero_removed, scrape_all_removed
    data = scrape_hero_removed("reaper")
"""

import json
import os
import re
import sys
from bs4 import BeautifulSoup
import requests

# ── 路径常量 ──
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DATA_FILE = os.path.join(_PROJECT_ROOT, "coach", "hero_db", "data.py")
STATS_CACHE = os.path.join(_PROJECT_ROOT, "coach", "hero_db", "stats_cache")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# h3 id 后缀 → 类型映射
_TYPE_MAP = {
    "被动": "被动",
    "主要攻击": "技能（主要攻击）",
    "辅助攻击": "技能（辅助攻击）",
    "技能1": "技能（技能1）",
    "技能2": "技能（技能2）",
    "终极技能": "技能（终极技能）",
    "次级威能-左": "次级威能",
    "次级威能-右": "次级威能",
    "主要威能-左": "主要威能",
    "主要威能-右": "主要威能",
}


def _get_hero_ids() -> list[str]:
    """从 data.py 中提取所有英雄 id。"""
    ids = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r'\s+"(.+)":\s*\{', line)
            if m:
                ids.append(m.group(1))
    return sorted(ids)


def _extract_type_from_h3id(h3_id: str) -> str:
    """从 h3 的 id 属性中提取类型描述。"""
    for suffix, label in _TYPE_MAP.items():
        if h3_id.endswith(suffix):
            return label
    return "技能"


def _parse_date_section(container_soup: BeautifulSoup) -> dict:
    """从容器 HTML 的"其他内容"tab 中提取日期/赛季信息。

    Returns:
        {"season": str, "date": str, "note": str} 各字段可能为空
    """
    result = {"season": "", "date": "", "note": ""}

    # 方法1: 在 tabset 中找包含"其他内容"的 tab panel
    # 结构: <tabset><template v-slot:tabs=""><li>其他内容</li>...
    #       <template v-slot:content=""><div class="tabset-panel">...
    # tabset 的内容里找 <li><p>...</p></li> 的文本
    tabset = container_soup.find("tabset")
    if tabset:
        # 尝试找到所有 tab panels
        panels = tabset.select("div.tabset-panel")
        # 从 tabs 的标签名找"其他内容"对应的索引
        tabs_template = tabset.find("template", attrs={"v-slot:tabs": True})
        target_idx = -1
        if tabs_template:
            li_items = tabs_template.find_all("li")
            for i, li in enumerate(li_items):
                if "其他内容" in li.get_text():
                    target_idx = i
                    break

        if target_idx >= 0 and target_idx < len(panels):
            panel = panels[target_idx]
            _extract_date_from_panel(panel, result)
        else:
            # 备选：遍历所有 panel，找包含日期的
            for panel in panels:
                _extract_date_from_panel(panel, result)
                if result["date"] or result["season"]:
                    break
    else:
        # 方法2: 直接在 container HTML 文本中搜索日期模式
        _extract_date_from_text(str(container_soup), result)

    return result


def _extract_date_from_panel(panel, result: dict):
    """从 tab panel 中提取赛季/日期信息。"""
    text = panel.get_text(separator="\n", strip=True)
    _extract_date_from_text(text, result)


def _extract_date_from_text(text: str, result: dict):
    """从纯文本中提取赛季/日期信息。

    支持格式:
      - "2025/02/19（第15赛季）加入，2025/08/27（第18赛季）移除。"
      - "2025/08/27（第18赛季）移除。"
      - "2025/08/27（第18赛季）加入"
    """
    # 匹配 "加入" 和/或 "移除" 的完整句子
    # 尝试找到包含赛季的完整日期描述
    date_pattern = re.compile(
        r"(\d{4}/\d{2}/\d{2}（第\d+赛季）.*?)(?:[。，]|$)"
    )
    # 优先找 "移除" 相关的日期
    remove_match = re.search(
        r"(\d{4}/\d{2}/\d{2})（第(\d+)赛季）.*?移除", text
    )
    add_match = re.search(
        r"(\d{4}/\d{2}/\d{2})（第(\d+)赛季）.*?加入", text
    )

    # 提取完整句子作为 note
    full_sentences = date_pattern.findall(text)
    full_text = "；".join(s.strip() for s in full_sentences if s.strip())

    if remove_match:
        result["date"] = remove_match.group(1)
        result["season"] = f"第{remove_match.group(2)}赛季"
    elif add_match:
        # 如果只有加入日期没有移除，可能是技能变为基础技能
        result["date"] = add_match.group(1)
        result["season"] = f"第{add_match.group(2)}赛季"

    # 如果有加入+移除的完整句子，用完整句子作为 note
    if not full_text:
        # 回退：只要是包含赛季的文字就提取
        m = re.search(r"(\d{4}/\d{2}/\d{2}（第\d+赛季）[\s\S]{0,50}?)(?:[。，]|加入|移除)", text)
        if m:
            full_text = m.group(1)

    if full_text:
        result["note"] = full_text
    elif result["season"]:
        result["note"] = result["season"]
    elif remove_match:
        result["note"] = f"{remove_match.group(1)}（第{remove_match.group(2)}赛季）移除"


def _clean_name(full_name: str) -> str:
    """从完整技能名中移除多余空白。"""
    return full_name.strip()


def scrape_hero_removed(hero_id: str) -> list[dict]:
    """抓取单个英雄的已移除内容。

    Args:
        hero_id: 英雄 id，如 "reaper"

    Returns:
        list[dict]: 已移除条目列表，格式:
            [{"name": str, "type": str, "season": str, "date": str, "note": str}]
    """
    url = f"https://overlab.cn/zh/wiki/hero/{hero_id}/removed"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = "utf-8"

        # 404 或重定向到首页则跳过
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            return []

        html = r.text

        # 检查页面是否包含有效内容（短页面通常是无内容的 404 兜底页）
        if "已移除内容" not in html or len(html) < 5000:
            return []

    except requests.RequestException:
        return []

    soup = BeautifulSoup(html, "html.parser")

    # 找到所有 sect1 块
    sections = soup.select("div.sect1")

    results = []
    for sect in sections:
        h2 = sect.find("h2")
        if not h2:
            continue
        section_title = h2.get_text(strip=True)
        # 只处理"英雄技能"和"英雄威能"部分
        is_skill = "英雄技能" in section_title
        is_talent = "英雄威能" in section_title
        if not is_skill and not is_talent:
            continue

        # 在此 section 中找容器
        containers = sect.select("div.row.overlab-wiki-hero-0-英雄技能-容器")
        for container in containers:
            entry = _parse_container(container, is_talent=is_talent)
            if entry:
                results.append(entry)

    return results


def _parse_container(container_soup: BeautifulSoup, is_talent: bool) -> dict | None:
    """解析单个容器 div，提取已移除条目。"""
    h3 = container_soup.find("h3")
    if not h3:
        return None

    # 提取 h3 id 用于类型判断
    h3_id = h3.get("id", "")
    if not h3_id:
        return None

    # 提取名称（在 h3 > div.paragraph > p 中）
    name_p = h3.select_one("div.paragraph > p")
    if not name_p:
        return None
    name = _clean_name(name_p.get_text(strip=True))

    # 确定类型
    entry_type = _extract_type_from_h3id(h3_id)
    if not entry_type:
        entry_type = "威能" if is_talent else "技能"

    # 提取日期信息
    date_info = _parse_date_section(container_soup)

    entry = {
        "name": name,
        "type": entry_type,
        "season": date_info["season"],
        "date": date_info["date"],
        "note": date_info["note"],
    }

    return entry


def scrape_all_removed(hero_ids: list[str] | None = None) -> dict[str, list[dict]]:
    """抓取所有（或指定）英雄的已移除内容。

    Args:
        hero_ids: 英雄 ID 列表；为 None 时抓取 data.py 中所有英雄

    Returns:
        dict: {hero_id: [entry, ...], ...}
    """
    os.makedirs(STATS_CACHE, exist_ok=True)

    if hero_ids is None:
        hero_ids = _get_hero_ids()

    all_data = {}
    total = len(hero_ids)
    for i, hid in enumerate(hero_ids):
        out_path = os.path.join(STATS_CACHE, f"{hid}_removed.json")

        print(f"[{i+1}/{total}] {hid:25s}...", end=" ", flush=True)

        try:
            entries = scrape_hero_removed(hid)
            if entries:
                all_data[hid] = entries
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(entries, f, ensure_ascii=False, indent=2)
                print(f"{len(entries)} 条 -> {os.path.basename(out_path)}")
            else:
                print("无内容（跳过）")
                # 保存空列表以便区分"已抓取无内容"和"未抓取"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"错误: {e}")

    return all_data


def main():
    """命令行入口。"""
    if len(sys.argv) > 1:
        hero_ids = [a for a in sys.argv[1:] if not a.startswith("-")]
    else:
        hero_ids = None

    print("=" * 60)
    print("overlab.cn 英雄已移除内容抓取器")
    if hero_ids:
        print(f"指定英雄: {', '.join(hero_ids)}")
    else:
        print("目标: 所有英雄（从 data.py 读取）")
    print(f"输出目录: {STATS_CACHE}")
    print("=" * 60)

    all_data = scrape_all_removed(hero_ids)

    total_entries = sum(len(v) for v in all_data.values())
    heroes_with_content = sum(1 for v in all_data.values() if v)
    print(f"\n完成！共处理 {len(all_data)} 个英雄，其中 {heroes_with_content} 个有已移除内容，共 {total_entries} 条")

    return 0


if __name__ == "__main__":
    sys.exit(main())
