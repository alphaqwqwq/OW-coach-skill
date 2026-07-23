"""Extract aliases from cached hero pages: 中文名, 英文名, 俗称."""
import re, json, os, sys
from glob import glob

CACHE = r"d:\workspace\ow-coach\coach\hero_db\scrape_cache"
DATA_PY = r"d:\workspace\ow-coach\coach\hero_db\data.py"

# Structure:
#   <div class="...-标签">中文名</div>
#   <div class="...-内容"><div class="paragraph"><p>NAME</p></div></div>

PAT_TAG_VAL = re.compile(
    r'class="[^"]*标签[^"]*"[^>]*>\s*(\S+?)\s*</div>\s*'
    r'<div[^>]*class="[^"]*内容[^"]*"[^>]*>.*?'
    r'<p>(.*?)</p>',
    re.DOTALL
)

aliases = {}
for fpath in sorted(glob(os.path.join(CACHE, "*.html"))):
    hid = os.path.basename(fpath).replace(".html", "")
    html = open(fpath, encoding="utf-8").read()

    # Extract all tag-value pairs from the hero info section
    info = {}
    for m in PAT_TAG_VAL.finditer(html):
        tag = m.group(1).strip()
        val = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        info[tag] = val

    name_cn = info.get("中文名", "")
    name_en = info.get("英文名", "")
    alias_raw = info.get("俗称", "")

    alias_list = [a.strip() for a in re.split(r'[,，/、\s]+', alias_raw) if a.strip()]

    keys = []
    if name_cn:
        keys.append(name_cn)
    if name_en:
        keys.append(name_en)
    if hid not in keys:
        keys.append(hid)
    keys.extend(a for a in alias_list if a not in keys)

    aliases[hid] = keys
    print(f"{hid:20s} cn={name_cn:8s} en={name_en:15s} nick={alias_list}")

# Now update data.py
sys.path.insert(0, r"d:\workspace\ow-coach")
for mod in list(sys.modules.keys()):
    if "coach.hero_db" in mod:
        del sys.modules[mod]

from coach.hero_db.data import HEROES

for hid in sorted(HEROES.keys()):
    if hid in aliases and len(aliases[hid]) > 1:
        HEROES[hid]["keys"] = aliases[hid]
    elif hid in HEROES:
        # If only English name extracted, at least add the hid
        cn = aliases.get(hid, [""])[0]
        if cn:
            HEROES[hid]["keys"] = [cn, hid]

# Write new data.py
lines = [
    '"""英雄知识库 — 数据层。',
    "来源: https://overlab.cn/zh/wiki",
    "自动生成于: 2026-07-23",
    '"""',
    "",
    "HEROES: dict[str, dict] = {",
]

for hid in sorted(HEROES.keys()):
    h = HEROES[hid]
    src = h.get("source", f"https://overlab.cn/zh/wiki/hero/{hid}")
    upd = h.get("updated", "2026-07-23")
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

with open(DATA_PY, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\nUpdated {DATA_PY}")
print(f"Total heroes: {len(HEROES)}")
