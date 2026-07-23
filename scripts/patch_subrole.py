"""Patch data.py: add subrole, fandom_id, and clean up skills display."""
import sys, json, os

sys.path.insert(0, r"d:\workspace\ow-coach")
for mod in list(sys.modules.keys()):
    if "coach" in mod:
        del sys.modules[mod]

from coach.hero_db.data import HEROES
from coach.hero_db.fandom import PAGE_MAP

# Subrole mapping (from overlab subrole tags, verified against Fandom)
SUBROLE = {
    # 重装
    "orisa": "斗士", "mauga": "斗士", "roadhog": "斗士", "junker-queen": "斗士", "zarya": "斗士",
    "dva": "先锋", "winston": "先锋", "wrecking-ball": "先锋", "doomfist": "先锋", "hazard": "先锋",
    "domina": "铁壁", "reinhardt": "铁壁", "ramattra": "铁壁", "sigma": "铁壁",
    # 输出
    "tracer": "奇袭", "reaper": "奇袭", "genji": "奇袭", "venture": "奇袭",
    "anran": "奇袭", "vendetta": "奇袭", "shion": "奇袭",
    "pharah": "侦查", "sombra": "侦查", "echo": "侦查", "freja": "侦查", "sierra": "侦查",
    "mei": "专业", "bastion": "专业", "junkrat": "专业", "torbjorn": "专业",
    "symmetra": "专业", "emre": "专业", "soldier-76": "专业",
    "hanzo": "神准", "widowmaker": "神准", "ashe": "神准", "cassidy": "神准", "sojourn": "神准",
    # 支援
    "moira": "医疗", "mercy": "医疗", "lifeweaver": "医疗", "kiriko": "医疗", "mizuki": "医疗",
    "brigitte": "生存", "illari": "生存", "juno": "生存", "wuyang": "生存",
    "ana": "战术", "baptiste": "战术", "zenyatta": "战术", "lucio": "战术", "jetpack-cat": "战术",
}

# Generate updated data.py
lines = [
    '"""英雄知识库 — 数据层。',
    "来源: overlab.cn (技能数据) + overwatch.fandom.com (策略文本)",
    "自动生成于: 2026-07-23",
    '"""',
    "",
    "HEROES: dict[str, dict] = {",
]

for hid in sorted(HEROES.keys()):
    h = HEROES[hid]
    src = h.get("source", f"https://overlab.cn/zh/wiki/hero/{hid}")
    upd = h.get("updated", "2026-07-23")
    role = h["role"]
    hp = h["hp"]
    subrole = SUBROLE.get(hid, "")
    fandom_page = PAGE_MAP.get(hid, "")

    # Build summary line from role+subrole
    summary_parts = []
    if role:
        summary_parts.append(role)
    if subrole:
        summary_parts.append(subrole)
    summary = "·".join(summary_parts) if summary_parts else ""

    lines.append("")
    lines.append(f'    "{hid}": {{')
    lines.append(f'        "keys": {json.dumps(h["keys"], ensure_ascii=False)},')
    lines.append(f'        "role": "{role}",')
    if subrole:
        lines.append(f'        "subrole": "{subrole}",')
    lines.append(f'        "hp": {hp},')
    lines.append(f'        "summary": "{summary}",')
    if fandom_page:
        lines.append(f'        "fandom_id": "{fandom_page}",')
    lines.append(f'        "skills": [')
    for s in h["skills"]:
        sk = {"key": s["key"], "name": s["name"], "desc": s.get("desc", "")}
        if s.get("cd"):
            sk["cd"] = s["cd"]
        if s.get("note"):
            sk["note"] = s["note"]
        lines.append(f'            {json.dumps(sk, ensure_ascii=False)},')
    lines.append(f'        ],')
    lines.append(f'        "counter": "",')
    lines.append(f'        "source": "{src}",')
    lines.append(f'        "updated": "{upd}",')
    lines.append(f'    }},')

lines.append("}")
lines.append("")
lines.append("ALIAS: dict[str, str] = {}")
lines.append("for hid, hdata in HEROES.items():")
lines.append("    for k in hdata['keys']:")
lines.append("        ALIAS[k.lower()] = hid")

out = r"d:\workspace\ow-coach\coach\hero_db\data.py"
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Updated {out}")
print(f"Heroes in DB: {len(HEROES)}")
print(f"Heroes with subrole: {sum(1 for h in SUBROLE if h in HEROES)}")
print(f"Heroes with fandom: {sum(1 for h in PAGE_MAP if h in HEROES)}")
