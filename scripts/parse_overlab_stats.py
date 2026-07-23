"""从 overlab.cn HTML 缓存中提取英雄技能的结构化数值数据。

用法:
    python scripts/parse_overlab_stats.py              # 解析所有英雄
    python scripts/parse_overlab_stats.py reaper       # 仅解析指定英雄
    python scripts/parse_overlab_stats.py ana baptiste # 解析多个英雄

作为模块导入:
    from parse_overlab_stats import parse_hero_html, parse_hero_file
    data = parse_hero_file("coach/hero_db/scrape_cache/reaper.html")
"""

import json
import os
import re
import sys
from glob import glob
from bs4 import BeautifulSoup

# ── 路径常量 ──
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
SCRAPE_CACHE = os.path.join(_PROJECT_ROOT, "coach", "hero_db", "scrape_cache")
STATS_CACHE = os.path.join(_PROJECT_ROOT, "coach", "hero_db", "stats_cache")


# ── 标签名映射（中文 -> 英文短名，便于程序化访问）──
# 不强制使用，但输出时保留两份：中文原标签和英文短名
_LABEL_MAP = {
    "子弹类型": "ammo_type",
    "伤害量": "damage",
    "伤害衰减": "falloff",
    "扩散角度": "spread",
    "弹匣容量": "magazine",
    "攻击频率": "fire_rate",
    "换弹时间": "reload",
    "能否暴击": "crit",
    "冷却时间": "cooldown",
    "持续时间": "duration",
    "移动速度": "move_speed",
    "技能类型": "skill_type",
    "生命汲取": "lifesteal",
    "消耗弹药": "ammo_cost",
    "前摇后摇": "windup_winddown",
    "前摇": "windup",
    "后摇": "winddown",
    "所需充能": "ult_cost",
    "自然充能": "passive_charge",
    "技能范围": "radius",
    "最大距离": "max_range",
    "治疗量": "healing",
    "每秒治疗量": "hps",
    "护盾值": "shield",
    "减伤": "damage_reduction",
    "持续时间上限": "max_duration",
    "投射物速度": "projectile_speed",
    "弹药上限": "max_ammo",
}


def _clean_skill_name(full_name: str) -> str:
    """从完整技能名中移除括号内的类型后缀，如 '地狱火霰弹枪（主要攻击）' -> '地狱火霰弹枪'"""
    return re.sub(r'\s*[（(][^）)]*[）)]\s*', '', full_name).strip()


def _get_text_from_p(parent) -> str:
    """从元素内的第一个 <p> 提取纯文本。

    BS4 4.14.3 中 <template> 内内容的 text 节点类型为 TemplateString，
    get_text() 无法正确提取，但 .string 可以。这里先尝试 .string，
    失败时回退到 get_text()。
    """
    p = parent.find('p') if parent else None
    if p is None:
        return ""
    # .string 对 TemplateString 有效，对普通 NavigableString 也有效
    if p.string is not None:
        return p.string.strip()
    # 回退方案：拼接所有字符串
    parts = [str(s).strip() for s in p.strings if str(s).strip()]
    return " ".join(parts) if parts else ""


def parse_hero_html(soup: BeautifulSoup) -> dict:
    """从 BeautifulSoup 对象解析所有技能的数值数据。

    Args:
        soup: 已解析的 BeautifulSoup 对象

    Returns:
        dict: {skill_key: {label: value, ...}, ...}
    """
    result = {}

    containers = soup.select('div.row.overlab-wiki-hero-0-英雄技能-容器')

    for container in containers:
        # ── 1. 提取英文锚点作为技能 key ──
        anchors = container.find_all('a', class_='overlab-暗锚')
        if len(anchors) < 2:
            continue

        # 优先取英文锚点（第二个 a），如果为 "undefined" 或空则回退到中文锚点
        skill_key = anchors[1].get('id', '').strip()
        if not skill_key or skill_key == 'undefined':
            skill_key = anchors[0].get('id', '').strip()
        if not skill_key or skill_key == 'undefined':
            # 最后备选：从 h3 的 id 生成 key
            h3 = container.find('h3')
            if h3:
                h3_id = h3.get('id', '').strip()
                if h3_id and h3_id != 'undefined':
                    # 去掉末尾的类型标记，如 "地狱火霰弹枪主要攻击" -> "地狱火霰弹枪"
                    skill_key = re.sub(r'(主要攻击|辅助攻击|技能[12]|终极技能|被动|次级威能-[左右]|主要威能-[左右])$', '', h3_id)
            if not skill_key or skill_key == 'undefined':
                continue

        # ── 2. 提取技能中文名 ──
        h3 = container.find('h3')
        if not h3:
            continue

        full_name = _get_text_from_p(h3)
        clean_name = _clean_skill_name(full_name)

        # ── 3. 提取所有数值标签-值对 ──
        stats = {}
        info_divs = container.select('.overlab-wiki-hero-0-英雄简介-信息')

        for info in info_divs:
            label_div = info.find('div', class_='overlab-wiki-hero-0-英雄简介-信息-标签')
            content_div = info.find('div', class_='overlab-wiki-hero-0-英雄简介-信息-内容')

            # 有些信息行（如分隔栏）没有标签
            if not label_div or not content_div:
                continue

            label = _get_text_from_p(label_div)
            value = _get_text_from_p(content_div)

            # 跳过占位条目
            if not label or label == '-' or not value or value == '-':
                continue

            stats[label] = value

        # 跳过无数值的技能（如通用被动占位）
        if not stats:
            continue

        # 构建最终条目
        entry = {"_skill_name": clean_name}
        entry.update(stats)
        result[skill_key] = entry

    return result


def parse_hero_file(filepath: str) -> dict:
    """从 HTML 文件路径解析英雄技能数值数据。

    Args:
        filepath: HTML 文件路径

    Returns:
        dict: {skill_key: {label: value, ...}, ...}
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    return parse_hero_html(soup)


def parse_all_heroes(hero_ids: list[str] | None = None) -> dict[str, dict]:
    """解析 scrape_cache 中所有（或指定）英雄的 HTML 文件。

    Args:
        hero_ids: 要解析的英雄 ID 列表；为 None 时解析全部

    Returns:
        dict: {hero_id: {skill_key: {label: value, ...}, ...}, ...}
    """
    os.makedirs(STATS_CACHE, exist_ok=True)

    if hero_ids:
        html_files = []
        for hid in hero_ids:
            fp = os.path.join(SCRAPE_CACHE, f"{hid}.html")
            if os.path.exists(fp):
                html_files.append((hid, fp))
            else:
                print(f"  [跳过] 未找到 {hid}.html")
    else:
        pattern = os.path.join(SCRAPE_CACHE, "*.html")
        html_files = [
            (os.path.splitext(os.path.basename(p))[0], p)
            for p in glob(pattern)
        ]
        html_files.sort(key=lambda x: x[0])

    all_data = {}
    for hid, fp in html_files:
        try:
            data = parse_hero_file(fp)
            if data:
                all_data[hid] = data
            else:
                print(f"  [空] {hid} - 未提取到技能数值")

            # 保存到 stats_cache
            out_path = os.path.join(STATS_CACHE, f"{hid}_stats.json")
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  [OK] {hid:25s} -> {os.path.basename(out_path):30s} ({len(data)} 个技能)")

        except Exception as e:
            print(f"  [错误] {hid}: {e}")

    return all_data


def main():
    """命令行入口。"""
    if len(sys.argv) > 1:
        hero_ids = [a for a in sys.argv[1:] if not a.startswith('-')]
    else:
        hero_ids = None

    print("=" * 60)
    print(f"overlab.cn 英雄技能数值解析器")
    print(f"来源目录: {SCRAPE_CACHE}")
    print(f"输出目录: {STATS_CACHE}")
    print("=" * 60)

    all_data = parse_all_heroes(hero_ids)

    total_skills = sum(len(v) for v in all_data.values())
    print(f"\n完成！共解析 {len(all_data)} 个英雄, {total_skills} 个技能")

    return 0


if __name__ == '__main__':
    sys.exit(main())
