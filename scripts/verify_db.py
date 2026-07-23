"""Verify hard DB"""
import sys, os
sys.path.insert(0, "d:\\workspace\\ow-coach")

from coach.hero_db.lookup import find_hero, get_hero_info_text, detect_heroes
from coach.hero_db.data import HEROES

print(f"Total heroes in DB: {len(HEROES)}")

ids = detect_heroes("我拉玛刹打对面奥丽莎和安娜，队友用源氏和猎空")
print(f"Detected in comp question: {ids}")

for query in ["安娜", "emre", "探奇", "源氏", "奥丽莎"]:
    h = find_hero(query)
    if h:
        print(f"  {query:6s} -> skills={len(h['skills'])} HP={h['hp']}")
    else:
        print(f"  {query:6s} -> NOT FOUND")

from coach.agent import build_prompt
prompt = build_prompt("comp_test", [], "奶位选安娜还是朱诺比较搭？")
has_hero = "英雄档案" in prompt
has_ana = "安娜" in prompt
has_juno = "朱诺" in prompt or "juno" in prompt
print(f"Hero section injected: {has_hero}")
print(f"Ana data: {has_ana}")
print(f"Juno data: {has_juno}")

# list hero names
print("\nHero roster:")
for hid in sorted(HEROES.keys()):
    h = HEROES[hid]
    name = h["keys"][0]
    skills = len(h["skills"])
    role = h["role"]
    hp = h["hp"]
    marker = " <-- 0 skills" if skills == 0 else ""
    print(f"  {name:10s} ({hid:15s}) {role} HP={hp:3d} skills={skills}{marker}")
