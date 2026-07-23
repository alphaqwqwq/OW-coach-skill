"""导出英雄数据为前端可用的静态 JSON 文件。"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from coach.hero_db.data import HEROES

OUT = os.path.join(os.path.dirname(__file__), "..", "web", "public", "data")
os.makedirs(OUT, exist_ok=True)

# ====== 1. heroes.json — 所有英雄基本信息 ======
heroes_list = []
for hid, h in HEROES.items():
    entry = {
        "id": hid,
        "keys": h["keys"],
        "name_cn": h.get("name_cn", ""),
        "role": h["role"],
        "subrole": h.get("subrole", ""),
        "summary": h.get("summary", ""),
        "hp": h["hp"],
        "skills": h["skills"],
        "counter": h.get("counter", ""),
        "source": h.get("source", ""),
        "updated": h.get("updated", ""),
    }
    heroes_list.append(entry)

with open(os.path.join(OUT, "heroes.json"), "w", encoding="utf-8") as f:
    json.dump(heroes_list, f, ensure_ascii=False, indent=2)
print(f"导出 heroes.json: {len(heroes_list)} 个英雄")


# ====== 2. cn_names.json — 中文名映射 ======
CN_NAMES = {
    "死神": "reaper", "安娜": "ana", "雾子": "kiriko",
    "天使": "mercy", "源氏": "genji", "猎空": "tracer",
    "半藏": "hanzo", "半蔵": "hanzo",
    "莱因哈特": "reinhardt",
    "士兵76": "soldier76", "76": "soldier76",
    "黑百合": "widowmaker", "法老之鹰": "pharah",
    "法拉": "pharah", "麦克雷": "cassidy", "卡西迪": "cassidy",
    "路霸": "roadhog", "堡垒": "bastion", "托比昂": "torbjorn",
    "秩序之光": "symmetra", "禅雅塔": "zenyatta", "和尚": "zenyatta",
    "查莉娅": "zarya", "卢西奥": "lucio", "dj": "lucio",
    "狂鼠": "junkrat", "D.Va": "dva", "dva": "dva",
    "美": "mei", "小美": "mei", "温斯顿": "winston",
    "奥丽莎": "orisa", "莫伊拉": "moira",
    "布丽吉塔": "brigitte", "布里吉塔": "brigitte",
    "西格玛": "sigma", "艾什": "ash", "巴蒂斯特": "baptiste",
    "回声": "echo", "索杰恩": "sojourn",
    "渣客女王": "junkerqueen", "女王": "junkerqueen",
    "拉玛刹": "ramattra", "生命之梭": "lifeweaver",
    "织命": "lifeweaver", "伊拉瑞": "illari",
    "骇灾": "hazard", "探奇": "venture", "地鼠": "venture",
    "弗蕾娅": "freja", "芙蕾雅": "freja",
    "西拉": "sierra", "埃姆雷": "emre",
    "艾姆雷": "emre", "安燃": "anran",
    "斩仇": "shion", "无漾": "mizuki",
    "喷火机甲": "jetpack-cat", "喷火猫": "jetpack-cat",
}

with open(os.path.join(OUT, "cn_names.json"), "w", encoding="utf-8") as f:
    json.dump(CN_NAMES, f, ensure_ascii=False, indent=2)
print(f"导出 cn_names.json: {len(CN_NAMES)} 条映射")


# ====== 3. 复制 stats_cache 数据 ======
stats_src = os.path.join(os.path.dirname(__file__), "..", "coach", "hero_db", "stats_cache")
stats_dst = os.path.join(OUT, "stats")
os.makedirs(stats_dst, exist_ok=True)
for old_f in os.listdir(stats_dst):
    os.remove(os.path.join(stats_dst, old_f))

count_stats = 0
if os.path.exists(stats_src):
    for fname in os.listdir(stats_src):
        if fname.endswith("_stats.json"):
            with open(os.path.join(stats_src, fname), encoding="utf-8") as f:
                data = json.load(f)
            with open(os.path.join(stats_dst, fname), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            count_stats += 1
print(f"导出 stats: {count_stats} 个文件")


# ====== 4. 复制 fandom_cache 策略文本 ======
fandom_src = os.path.join(os.path.dirname(__file__), "..", "coach", "hero_db", "fandom_cache")
fandom_dst = os.path.join(OUT, "fandom")
os.makedirs(fandom_dst, exist_ok=True)
# Clean destination to prevent stale files (case-sensitivity issues on deploy)
for old_f in os.listdir(fandom_dst):
    os.remove(os.path.join(fandom_dst, old_f))

# Fandom page title → hero ID mapping for non-trivial cases
FANDOM_ID_MAP = {
    "D.Va": "dva",
    "Jetpack_Cat": "jetpack-cat",
    "Junker_Queen": "junker-queen",
    "L%C3%BAcio": "lucio",
    "Soldier: 76": "soldier-76",
    "Torbj%C3%B6rn": "torbjorn",
    "Wrecking_Ball": "wrecking-ball",
}

count_fandom = 0
if os.path.exists(fandom_src):
    for fname in os.listdir(fandom_src):
        if not fname.endswith("_strategy.json"):
            continue
        # Extract page title from fname
        page_title = fname[: -len("_strategy.json")]

        # Determine target hero ID
        if page_title in FANDOM_ID_MAP:
            hid = FANDOM_ID_MAP[page_title]
        else:
            # Default: lowercase the page title to get hero ID
            hid = page_title.lower()

        # Skip if hero not in db
        if hid not in HEROES:
            print(f"  [跳过] {fname} → hero '{hid}' 不在数据库中")
            continue

        # Read and re-save with correct filename
        with open(os.path.join(fandom_src, fname), encoding="utf-8") as f:
            data = json.load(f)
        out_name = f"{hid}_strategy.json"
        with open(os.path.join(fandom_dst, out_name), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        count_fandom += 1
print(f"导出 fandom: {count_fandom} 个文件")


# ====== 5. prompts.json — 打包提示词 ======
prompts_dir = os.path.join(os.path.dirname(__file__), "..", "coach", "prompts")
prompts = {}
for fname in ["system.md", "framework.md", "knowledge.md"]:
    path = os.path.join(prompts_dir, fname)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            prompts[fname.replace(".md", "")] = f.read()

with open(os.path.join(OUT, "prompts.json"), "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2)
print(f"导出 prompts: {list(prompts.keys())}")

print("\n所有数据导出完成！")
