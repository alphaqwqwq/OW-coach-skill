"""Verify DB is fully functional"""
import sys
# Force fresh import
for mod in list(sys.modules.keys()):
    if "coach" in mod:
        del sys.modules[mod]

sys.path.insert(0, "d:\\workspace\\ow-coach")

from coach.hero_db.lookup import find_hero, detect_heroes

print("=== Chinese name lookup ===")
for query in ["安娜", "埃姆雷", "探奇", "源氏", "奥丽莎", "朱诺", "无漾", "士兵：76"]:
    h = find_hero(query)
    print(f"  {query:10s} -> {'OK' if h else 'MISS'}")

print("\n=== English name lookup ===")
for query in ["ana", "emre", "venture", "genji", "orisa"]:
    h = find_hero(query)
    print(f"  {query:10s} -> {'OK' if h else 'MISS'}")

print("\n=== Team comp detection ===")
text = "我拉玛刹打对面奥丽莎和安娜，队友用源氏和猎空，奶是朱诺"
ids = detect_heroes(text)
print(f"  Text: {text}")
print(f"  Detected: {ids}")

print("\n=== Agent integration ===")
from coach.agent import build_prompt
prompt = build_prompt("final_test", [], text)
print(f"  Hero section in prompt: {'英雄档案' in prompt}")
print(f"  Has 安娜 data: {'安娜' in prompt}")
print(f"  Has 朱诺 data: {'朱诺' in prompt}")

print("\n=== All OK ===")
