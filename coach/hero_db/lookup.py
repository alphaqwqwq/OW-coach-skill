"""英雄知识库 — 查询层。
用法:
    from coach.hero_db.lookup import find_hero, get_hero_info, get_hero_info_text

    # 搜索英雄
    hero = find_hero("埃姆雷")  # 别名匹配
    hero = find_hero("emre")    # 英文名

    # 获取格式化文本（适合注入提示词）
    text = get_hero_info_text("emre")
"""

from .data import HEROES, ALIAS


def find_hero(query: str) -> dict | None:
    """按中文名/英文名/俗称搜索英雄，返回数据 dict。"""
    q = query.strip().lower()
    if q in HEROES:
        return HEROES[q]
    hid = ALIAS.get(q)
    return HEROES.get(hid)


def get_hero_info(hid: str) -> dict | None:
    """按英文 id 获取英雄数据。"""
    return HEROES.get(hid)


def get_hero_info_text(query: str) -> str:
    """获取英雄信息格式化文本，适合注入提示词。"""
    hero = find_hero(query)
    if not hero:
        return ""

    lines = [
        f"{hero['keys'][0]} ({hero['keys'][1]}) — {hero['role']}·{hero.get('subrole','')}",
        f"生命值: {hero['hp']}",
        f"定位: {hero['summary']}",
        "",
        "技能:",
    ]
    for s in hero["skills"]:
        line = f"  [{s['key']}] {s['name']}: {s['desc']}"
        if s.get("cd") and s["cd"] != "—":
            line += f" (CD: {s['cd']})"
        if s.get("note"):
            line += f" | {s['note']}"
        lines.append(line)

    if hero.get("counter"):
        lines.extend(["", f"针对思路: {hero['counter']}"])

    lines.append("")
    lines.append(f"(数据来源: {hero['source']})")
    return "\n".join(lines)


def list_all_heroes() -> list[dict]:
    """列出所有英雄的基本信息。"""
    return [
        {
            "id": hid,
            "name": h["keys"][0],
            "name_en": h["keys"][1],
            "role": h["role"],
        }
        for hid, h in HEROES.items()
    ]


# 中文英雄名 → 英文 id 映射
# 从 overlab.cn 页面标题提取
CN_NAMES: dict[str, str] = {
    "死神": "reaper", "死神": "reaper",
    "安娜": "ana", "安娜": "ana",
    "雾子": "kiriko", "雾子": "kiriko",
    "天使": "mercy", "天使": "mercy",
    "源氏": "genji", "源氏": "genji",
    "猎空": "tracer", "猎空": "tracer",
    "半藏": "hanzo", "半蔵": "hanzo",
    "莱因哈特": "reinhardt",
    "士兵76": "soldier76", "76": "soldier76",
    "黑百合": "widowmaker", "黑百合": "widowmaker",
    "法老之鹰": "pharah", "法拉": "pharah",
    "麦克雷": "cassidy", "卡西迪": "cassidy",
    "路霸": "roadhog", "路霸": "roadhog",
    "堡垒": "bastion",
    "托比昂": "torbjorn",
    "秩序之光": "symmetra",
    "禅雅塔": "zenyatta", "和尚": "zenyatta",
    "查莉娅": "zarya",
    "卢西奥": "lucio", "dj": "lucio",
    "狂鼠": "junkrat",
    "D.Va": "dva", "dva": "dva",
    "美": "mei", "小美": "mei",
    "温斯顿": "winston",
    "奥丽莎": "orisa",
    "莫伊拉": "moira",
    "布丽吉塔": "brigitte", "布里吉塔": "brigitte",
    "西格玛": "sigma",
    "艾什": "ash",
    "巴蒂斯特": "baptiste",
    "回声": "echo",
    "索杰恩": "sojourn", "索杰恩": "sojourn",
    "渣客女王": "junkerqueen", "女王": "junkerqueen",
    "拉玛刹": "ramattra", "拉玛刹": "ramattra",
    "生命之梭": "lifeweaver", "织命": "lifeweaver",
    "伊拉瑞": "illari",
    "骇灾": "hazard", "骇灾": "hazard",
    "探奇": "venture", "地鼠": "venture",
    "弗蕾娅": "freja", "芙蕾雅": "freja",
    "西拉": "sierra",
    "埃姆雷": "emre", "艾姆雷": "emre",
    "安燃": "anran",
    "斩仇": "shion", "斩仇": "shion",
    "无漾": "mizuki",
    "喷火机甲": "jetpack-cat", "喷火猫": "jetpack-cat",
}

def detect_heroes(text: str) -> list[str]:
    """从一段文本中检测提到的英雄，返回英雄英文 id 列表。
    
    同时匹配英文 key 和中文名映射。
    """
    text_lower = text.lower()
    found = []
    for hid, hdata in HEROES.items():
        # 匹配英文 keys
        for key in hdata["keys"]:
            if key.lower() in text_lower:
                found.append(hid)
                break
        else:
            # 匹配中文名
            for cn_name, cn_hid in CN_NAMES.items():
                if cn_hid == hid and cn_name.lower() in text_lower:
                    found.append(hid)
                    break
    return found
