"""Verify final data.py HP values against wiki."""
import re, os, sys

CACHE = r"d:\workspace\ow-coach\coach\hero_db\scrape_cache"

def get_5v5_total_hp(html):
    idx = html.find("5v5 预设职责")
    if idx < 0:
        return 250
    section = html[idx:idx+2000]
    m = re.search(
        r'class="[^"]*生命值-total[^"]*".*?'
        r'class="[^"]*生命值-background[^"]*"[^>]*>\s*(\d+)\s*<',
        section, re.DOTALL
    )
    return int(m.group(1)) if m else 250

sys.path.insert(0, r"d:\workspace\ow-coach")
for mod in list(sys.modules.keys()):
    if "coach" in mod:
        del sys.modules[mod]

from coach.hero_db.data import HEROES

print(f"{'ID':20s} {'Name':10s} {'Role':6s} {'HP':>4s} {'WikiHP':>6s} {'Match':6s}")
print("-" * 55)

all_ok = True
for hid in sorted(HEROES.keys()):
    h = HEROES[hid]
    path = os.path.join(CACHE, f"{hid}.html")
    if os.path.exists(path):
        html = open(path, encoding="utf-8").read()
        wiki_hp = get_5v5_total_hp(html)
    else:
        wiki_hp = "no cache"
    
    db_hp = h["hp"]
    match = "OK" if db_hp == wiki_hp else f"{db_hp}≠{wiki_hp}"
    if db_hp != wiki_hp:
        all_ok = False
    
    name = h["keys"][0] if h["keys"] else "?"
    role = h["role"]
    print(f"{hid:20s} {name:10s} {role:6s} {db_hp:>4d} {str(wiki_hp):>6s} {match:6s}")

print(f"\n{'All HP correct!' if all_ok else 'SOME HP MISMATCHES!'}")
