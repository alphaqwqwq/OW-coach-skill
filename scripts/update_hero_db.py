"""
英雄知识库更新工具。
从 overlab.cn 抓取英雄技能数据，更新 coach/hero_db/data.py。

用法:
    python scripts/update_hero_db.py                # 更新所有英雄
    python scripts/update_hero_db.py --hero emre    # 只更新指定英雄
    python scripts/update_hero_db.py --list         # 列出可更新的英雄
    python scripts/update_hero_db.py --new          # 只更新 data.py 中尚未收录的英雄

依赖:
    pip install requests beautifulsoup4

注意: overlab.cn 是 HTML 页面，解析结果需要人工校对。
      本脚本输出的数据是"候选"，建议比对确认后替换到 data.py。
"""

import argparse, json, os, re, sys
from datetime import date

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("需要安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)

# 项目根目录
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PY = os.path.join(ROOT, "coach", "hero_db", "data.py")

WIKI_URL = "https://overlab.cn/zh/wiki"
HEADERS = {
    "User-Agent": "OW-Coach-HeroDB/1.0 (knowledge update tool)",
}

# 英雄中文名 → 英文 id 映射（从 overlab 页面提取得到）
# overlab 的 URL 模式: https://overlab.cn/zh/wiki/hero/{hero_id}
HERO_MAP: dict[str, str] = {
    # 重装
    "奥丽莎": "orisa",
    "D.Va": "dva",
    "末日铁拳": "doomfist",
    "毁灭之拳": "doomfist",
    "骇灾": "hazard",
    "金驭": "domina",
    "拉玛刹": "ramattra",
    "莱因哈特": "reinhardt",
    "路霸": "roadhog",
    "毛加": "mauga",
    "破坏球": "wrecking-ball",
    "西格玛": "sigma",
    "温斯顿": "winston",
    "渣客女王": "junker-queen",
    "查莉娅": "zarya",
    # 输出
    "艾什": "ashe",
    "埃姆雷": "emre",
    "堡垒": "bastion",
    "半藏": "hanzo",
    "法老之鹰": "pharah",
    "弗蕾娅": "freja",
    "芙蕾雅": "freja",
    "黑百合": "widowmaker",
    "黑影": "sombra",
    "回声": "echo",
    "卡西迪": "cassidy",
    "狂鼠": "junkrat",
    "猎空": "tracer",
    "美": "mei",
    "死神": "reaper",
    "士兵：76": "soldier-76",
    "士兵:76": "soldier-76",
    "索杰恩": "sojourn",
    "探奇": "venture",
    "托比昂": "torbjorn",
    "西拉": "sierra",
    "源氏": "genji",
    "斩仇": "vendetta",
    "秩序之光": "symmetra",
    "安燃": "anran",
    "死怨": "shion",
    # 支援
    "安娜": "ana",
    "巴蒂斯特": "baptiste",
    "布丽吉塔": "brigitte",
    "禅雅塔": "zenyatta",
    "飞天猫": "jetpack-cat",
    "卢西奥": "lucio",
    "莫伊拉": "moira",
    "生命之梭": "lifeweaver",
    "天使": "mercy",
    "雾子": "kiriko",
    "无漾": "wuyang",
    "无恙": "wuyang",
    "瑞稀": "mizuki",
    "伊拉锐": "illari",
    "朱诺": "juno",
}


def fetch_hero_list() -> dict[str, str]:
    """从 overlab 首页抓取英雄列表。"""
    resp = requests.get(WIKI_URL, headers=HEADERS, timeout=15)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    found = {}
    for a in soup.select("a[href*='/zh/wiki/hero/']"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if not text or not href:
            continue
        # Extract hero id from URL
        m = re.search(r"/hero/([\w-]+)", href)
        if m:
            found[text] = m.group(1)
    return found


def fetch_hero_page(hero_id: str) -> str | None:
    """抓取英雄页面。"""
    url = f"{WIKI_URL}/hero/{hero_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


def parse_hero_page(hero_id: str, html: str) -> dict:
    """从英雄页面解析数据，返回 dict（格式见 data.py）。"""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one("h1")
    name_cn = title.get_text(strip=True) if title else hero_id

    # 简单提取
    result = {
        "keys": [name_cn, hero_id],
        "skills": [],
        "source": f"{WIKI_URL}/hero/{hero_id}",
        "updated": date.today().isoformat(),
    }

    # Extract HP
    hp_match = re.search(r"(\d+)\s*$", html, re.MULTILINE)
    hp_section = ""
    for line in html.split("\n"):
        if "总生命值" in line:
            hp_section = line
            break

    # Extract skill sections
    skill_sections = soup.select("h3, h4")
    current_skill = None
    for tag in skill_sections:
        text = tag.get_text(strip=True)
        # Skip non-skill sections
        if any(x in text for x in ["英雄简介", "英雄威能", "角斗领域", "补丁说明", "英雄故事", "评论"]):
            current_skill = None
            continue

        # Try to determine key binding
        key = ""
        if "主要攻击" in text or "（左键）" in text:
            key = "左键"
        elif "辅助攻击" in text or "（右键）" in text:
            key = "右键"
        elif "技能1" in text or "（shift）" in text or "（Shift）" in text:
            key = "Shift"
        elif "技能2" in text or "（e）" in text or "（E）" in text:
            key = "E"
        elif "终极技能" in text or "（q）" in text or "（Q）" in text:
            key = "Q"
        elif "被动" in text:
            key = "被动"

        if key:
            current_skill = {"key": key, "name": text, "desc": "", "note": "", "cd": ""}
            result["skills"].append(current_skill)

    # Extract descriptions from paragraphs after headings
    for h in soup.select("h3, h4"):
        desc_parts = []
        for sibling in h.find_next_siblings():
            if sibling.name in ("h3", "h4", "hr"):
                break
            if sibling.name == "p":
                desc_parts.append(sibling.get_text(strip=True))
        if desc_parts:
            # Find the matching skill
            h_text = h.get_text(strip=True)
            for s in result["skills"]:
                if s["name"] == h_text:
                    s["desc"] = " | ".join(desc_parts[:3])
                    break

    return result


def main():
    parser = argparse.ArgumentParser(description="更新英雄知识库")
    parser.add_argument("--hero", help="只更新指定英雄 (英文 id)")
    parser.add_argument("--list", action="store_true", help="列出可更新的英雄")
    parser.add_argument("--new", action="store_true", help="只更新 data.py 中尚未收录的英雄")
    args = parser.parse_args()

    if args.list:
        print(f"overlab.cn 已知英雄 ({len(HERO_MAP)} 个):")
        for name, hid in sorted(HERO_MAP.items(), key=lambda x: x[1]):
            print(f"  {hid:20s} {name}")
        return

    if args.hero:
        ids_to_fetch = [args.hero]
    else:
        # Fetch all known heroes
        ids_to_fetch = sorted(set(HERO_MAP.values()))
        if args.new:
            # Filter out heroes already in data.py
            from coach.hero_db.data import HEROES
            ids_to_fetch = [h for h in ids_to_fetch if h not in HEROES]

    print(f"正在更新 {len(ids_to_fetch)} 个英雄...")

    for hid in ids_to_fetch:
        print(f"  {hid}...", end=" ", flush=True)
        html = fetch_hero_page(hid)
        if not html:
            print("抓取失败")
            continue
        data = parse_hero_page(hid, html)
        # Save to temp JSON for review
        out_dir = os.path.join(ROOT, "coach", "hero_db", "data")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{hid}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存到 data/{hid}.json")

    print("""
完成！抓取结果保存在 coach/hero_db/data/ 目录。
请人工校对后，将确认的数据合并到 coach/hero_db/data.py。

建议流程:
  1. 查看 data/*.json 检查技能解析是否准确
  2. 将准确的数据手动复制到 data.py 的 HEROES dict 中
  3. 删除错误的数据条目
""")


if __name__ == "__main__":
    main()
