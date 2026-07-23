"""Patch data.py with proper Chinese names."""
import sys, os
sys.path.insert(0, "d:\\workspace\\ow-coach")

from coach.hero_db.data import HEROES

NAME_MAP = {
    "ana": "安娜", "anran": "安燃", "ashe": "艾什", "baptiste": "巴蒂斯特",
    "bastion": "堡垒", "brigitte": "布丽吉塔", "cassidy": "卡西迪",
    "domina": "金驭", "doomfist": "末日铁拳", "dva": "D.Va",
    "echo": "回声", "emre": "埃姆雷", "freja": "弗蕾娅", "genji": "源氏",
    "hanzo": "半藏", "hazard": "骇灾", "illari": "伊拉锐",
    "jetpack-cat": "飞天猫", "junker-queen": "渣客女王", "junkrat": "狂鼠",
    "juno": "朱诺", "kiriko": "雾子", "lifeweaver": "生命之梭",
    "lucio": "卢西奥", "mauga": "毛加", "mei": "美",
    "mercy": "天使", "mizuki": "瑞稀", "moira": "莫伊拉",
    "orisa": "奥丽莎", "pharah": "法老之鹰", "ramattra": "拉玛刹",
    "reaper": "死神", "reinhardt": "莱因哈特", "roadhog": "路霸",
    "shion": "死怨", "sigma": "西格玛", "sojourn": "索杰恩",
    "soldier-76": "士兵：76", "sombra": "黑影", "symmetra": "秩序之光",
    "torbjorn": "托比昂", "tracer": "猎空", "vendetta": "斩仇",
    "venture": "探奇", "widowmaker": "黑百合", "winston": "温斯顿",
    "wrecking-ball": "破坏球", "wuyang": "无漾", "zarya": "查莉娅",
    "zenyatta": "禅雅塔",
}

# Update keys for each hero
for hid, h in HEROES.items():
    cn = NAME_MAP.get(hid, hid)
    h["keys"] = [cn, hid]

# Touch up HP for known mismatches
HP_FIX = {
    "juno": 225,
    "zenyatta": 200,
    "symmetra": 175,
    "echo": 200,
}
for hid, hp in HP_FIX.items():
    if hid in HEROES:
        HEROES[hid]["hp"] = hp

# Generate new data.py
lines = [
    '"""英雄知识库 — 数据层。',
    "来源: https://overlab.cn/zh/wiki",
    "自动生成于: 2026-07-23 (手动修正中文名+HP)",
    '"""',
    "",
    "HEROES: dict[str, dict] = {",
]

import json
for hid in sorted(HEROES.keys()):
    h = HEROES[hid]
    src = h["source"]
    upd = h["updated"]
    lines.append("")
    lines.append(f'    "{hid}": {{')
    lines.append(f'        "keys": {json.dumps(h["keys"], ensure_ascii=False)},')
    lines.append(f'        "role": "{h["role"]}",')
    lines.append(f'        "hp": {h["hp"]},')
    lines.append(f'        "summary": "",')
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

# Verify
from coach.hero_db.lookup import find_hero, detect_heroes
for query in ["安娜", "emre", "探奇", "源氏", "奥丽莎", "士兵：76"]:
    h = find_hero(query)
    print(f"  {query:10s} -> {'OK' if h else 'MISS'} (keys={h['keys'] if h else 'N/A'})")

ids = detect_heroes("我拉玛刹打对面奥丽莎和安娜，队友用源氏和猎空")
print(f"\nDetection: {ids}")
