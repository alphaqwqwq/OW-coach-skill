"""Scrape all heroes from overlab.cn and generate data.py.
Uses regex parsing because BeautifulSoup has issues with this site's nested h3 structure."""
import requests, re, json, os, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "coach", "hero_db", "data.py")
TMP = os.path.join(ROOT, "coach", "hero_db", "scrape_cache")
os.makedirs(TMP, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def parse_hp(html: str) -> int:
    """Extract HP from hero page."""
    m = re.search(r'class="[^"]*生命值-background[^"]*"\s*>\s*(\d+)', html)
    if m:
        return int(m.group(1))
    return 250


def parse_skills_regex(html: str) -> list[dict]:
    """Parse skills using regex on h3 blocks."""
    skills = []

    # h3 pattern — note: id comes BEFORE class in the actual HTML
    h3_pattern = re.compile(
        r'<h3[^>]*id="([^"]*)"[^>]*class="[^"]*英雄技能-技能名[^"]*"[^>]*>'
        r'.*?<p>(.*?)</p>'
        r'.*?</h3>'
        r'(.*?)(?=<h3[^>]*id="[^"]*"[^>]*class="[^"]*英雄技能-技能名|<h2|$)',
        re.DOTALL
    )

    for m in h3_pattern.finditer(html):
        hid = m.group(1)
        name_line = m.group(2).strip()
        desc_html = m.group(3).strip()

        if not name_line:
            continue

        # Skip 威能/talent sections
        if "威能" in name_line or "角斗领域" in name_line:
            continue

        key = ""
        if "主要攻击" in name_line:
            key = "左键"
        elif "辅助攻击" in name_line:
            key = "右键"
        elif "技能1" in name_line:
            key = "Shift"
        elif "技能2" in name_line:
            key = "E"
        elif "终极技能" in name_line:
            key = "Q"
        elif "被动" in name_line:
            key = "被动"

        if not key:
            continue

        name = name_line.strip()

        # Extract description from <p> tags in desc_html
        desc_parts = re.findall(r'<p>(.*?)</p>', desc_html, re.DOTALL)
        desc_list = []
        for d in desc_parts:
            text = re.sub(r'<[^>]+>', '', d).strip()
            if text:
                desc_list.append(text)

        # Extract CD
        cd_match = re.search(r'冷却时间[：:]\s*([^<\n]+)', desc_html)
        cd = cd_match.group(1).strip() if cd_match else ""

        # Extract key numbers
        note_parts = []
        dmg = re.search(r'伤害量[：:]\s*([^<\n]+)', desc_html)
        if dmg:
            note_parts.append(dmg.group(1).strip())
        heal = re.search(r'治疗量[：:]\s*([^<\n]+)', desc_html)
        if heal:
            note_parts.append("治疗:" + heal.group(1).strip())

        skill = {"key": key, "name": name, "desc": " | ".join(desc_list[:3])}
        if cd:
            skill["cd"] = cd
        if note_parts:
            skill["note"] = " | ".join(note_parts)
        skills.append(skill)

    return skills


# ── Step 1: Get hero list ──
print("Fetching hero list from overlab.cn...")
resp = requests.get("https://overlab.cn/zh/wiki", headers=HEADERS, timeout=15)
resp.encoding = "utf-8"
html = resp.text

href_pattern = re.compile(r'href="(/zh/wiki/hero/[\w-]+)"')
all_hero_links = href_pattern.findall(html)
unique_links = sorted(set(all_hero_links))

hero_list = {}
for link in unique_links:
    hid = link.split("/")[-1]
    idx = html.find(link)
    snippet = html[idx:idx+500]
    # Find hero name: look for the name inside <div class="hero-name"> or similar
    m = re.search(r'<div[^>]*>\s*(.{2,10})\s*</div>\s*<div', snippet[200:])
    name_cn = m.group(1).strip() if m else hid
    hero_list[hid] = name_cn

print(f"Found {len(hero_list)} heroes\n")

# ── Step 2: Fetch each hero page ──
HERO_DATA = {}
for i, (hid, name_cn) in enumerate(sorted(hero_list.items())):
    print(f"[{i+1}/{len(hero_list)}] {hid:25s} {name_cn[:12]:12s}...", end=" ", flush=True)

    cache_path = os.path.join(TMP, f"{hid}.html")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            html_page = f.read()
        print("(cached)", end=" ")
    else:
        try:
            url = f"https://overlab.cn/zh/wiki/hero/{hid}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.encoding = "utf-8"
            if r.status_code != 200:
                print(f"HTTP {r.status_code}")
                continue
            html_page = r.text
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(html_page)
        except Exception as e:
            print(f"error: {e}")
            continue

    hp = parse_hp(html_page)
    skills = parse_skills_regex(html_page)
    print(f"HP={hp} skills={len(skills)}")
    HERO_DATA[hid] = {"name_cn": name_cn, "hp": hp, "skills": skills}

print(f"\nFetched {len(HERO_DATA)} heroes")

# ── Step 3: Generate data.py ──
ROLE_MAP = {
    "orisa": "重装", "ramattra": "重装", "reinhardt": "重装", "sigma": "重装",
    "dva": "重装", "winston": "重装", "zarya": "重装", "roadhog": "重装",
    "junker-queen": "重装", "wrecking-ball": "重装", "doomfist": "重装",
    "mauga": "重装", "hazard": "重装", "domina": "重装",
    "tracer": "输出", "reaper": "输出", "genji": "输出", "pharah": "输出",
    "sombra": "输出", "echo": "输出", "mei": "输出", "bastion": "输出",
    "hanzo": "输出", "widowmaker": "输出", "junkrat": "输出",
    "torbjorn": "输出", "symmetra": "输出", "ashe": "输出",
    "cassidy": "输出", "sojourn": "输出", "venture": "输出",
    "freja": "输出", "soldier-76": "输出", "emre": "输出",
    "vendetta": "输出", "sierra": "输出", "anran": "输出", "shion": "输出",
    "ana": "支援", "mercy": "支援", "zenyatta": "支援", "lucio": "支援",
    "moira": "支援", "brigitte": "支援", "baptiste": "支援",
    "lifeweaver": "支援", "kiriko": "支援", "illari": "支援",
    "juno": "支援", "wuyang": "支援", "mizuki": "支援",
    "jetpack-cat": "支援",
}

print("\nGenerating data.py...")
lines = [
    '"""英雄知识库 — 数据层。',
    '来源: https://overlab.cn/zh/wiki',
    f'自动生成于: {date.today().isoformat()}',
    '"""',
    '',
    "HEROES: dict[str, dict] = {",
]

for hid in sorted(HERO_DATA.keys()):
    d = HERO_DATA[hid]
    name = d["name_cn"]
    role = ROLE_MAP.get(hid, "")
    hp = d["hp"]
    skills = d["skills"]
    url = f"https://overlab.cn/zh/wiki/hero/{hid}"

    lines.append("")
    lines.append(f'    "{hid}": {{')
    lines.append(f'        "keys": {json.dumps([name, hid], ensure_ascii=False)},')
    lines.append(f'        "role": "{role}",')
    lines.append(f'        "hp": {hp},')
    lines.append(f'        "summary": "",')
    lines.append(f'        "skills": [')
    for s in skills:
        sk = {"key": s.get("key", ""), "name": s.get("name", ""), "desc": s.get("desc", "")}
        if s.get("cd"):
            sk["cd"] = s["cd"]
        if s.get("note"):
            sk["note"] = s["note"]
        lines.append(f'            {json.dumps(sk, ensure_ascii=False)},')
    lines.append(f'        ],')
    lines.append(f'        "counter": "",')
    lines.append(f'        "source": "{url}",')
    lines.append(f'        "updated": "{date.today().isoformat()}",')
    lines.append(f'    }},')

lines.append("}")
lines.append("")
lines.append("ALIAS: dict[str, str] = {}")
lines.append("for hid, hdata in HEROES.items():")
lines.append("    for k in hdata['keys']:")
lines.append("        ALIAS[k.lower()] = hid")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Written to {OUT}")
print(f"Total heroes: {len(HERO_DATA)}")
