"""Session memory — conversation history + player profile (cross-session)."""
import json, os, re
from datetime import date

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
os.makedirs(DIR, exist_ok=True)

# ── Conversation history ──


def load(user_id: str) -> list[dict]:
    path = os.path.join(DIR, f"{user_id}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save(user_id: str, history: list[dict]) -> None:
    path = os.path.join(DIR, f"{user_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history[-20:], f, ensure_ascii=False, indent=2)


def add(user_id: str, user_msg: str, coach_msg: str) -> None:
    h = load(user_id)
    h.append({"role": "user", "content": user_msg})
    h.append({"role": "coach", "content": coach_msg})
    save(user_id, h)


# ── Player profile (cross-session memory) ──

PROFILE_BASE = {
    "diagnosed_issues": [],      # [{"issue": str, "status": str, "date": str}]
    "solutions_provided": [],    # [{"solution": str, "context": str, "date": str}]
    "coach_notes": "",           # free-form long-term observations
}


def profile_load(user_id: str) -> dict:
    path = os.path.join(DIR, f"{user_id}_profile.json")
    if os.path.exists(path):
        with open(path) as f:
            return {**PROFILE_BASE, **json.load(f)}
    return dict(PROFILE_BASE)


def profile_save(user_id: str, profile: dict) -> None:
    path = os.path.join(DIR, f"{user_id}_profile.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def profile_apply_updates(user_id: str, coach_response: str) -> str:
    """
    Parse optional [档案] section from coach response,
    merge into persistent player profile, return cleaned response.

    Expected format inside response:

        [档案]
        诊断+方案: <问题> → <方案>
        跟进: <问题> → 已有改善 / 仍存在问题
        笔记: <自由观察>
        [档案结束]
    """
    m = re.search(r'\[档案\]\s*(.*?)\[档案结束\]', coach_response, re.DOTALL)
    if not m:
        return coach_response

    clean = coach_response.replace(m.group(0), "").strip()
    lines = [
        l.strip().lstrip("- \t")
        for l in m.group(1).strip().split("\n")
        if l.strip()
    ]

    profile = profile_load(user_id)
    today = date.today().isoformat()
    changed = False

    for line in lines:
        # case: "诊断+方案: xxx → yyy" or "诊断: xxx → 方案: yyy"
        if "诊断" in line and "→" in line:
            parts = line.split("→", 1)
            diag = (
                parts[0]
                .replace("诊断", "")
                .replace("+方案", "")
                .replace(":", "")
                .strip()
            )
            sol = parts[1].strip() if len(parts) > 1 else ""
            profile["diagnosed_issues"].append(
                {"issue": diag, "status": "new", "date": today}
            )
            if sol:
                profile["solutions_provided"].append(
                    {"solution": sol, "context": diag, "date": today}
                )
            changed = True

        # case: "跟进: xxx → 已有改善" or "跟进: xxx → 仍存在问题"
        elif "跟进" in line and "→" in line:
            parts = line.split("→", 1)
            iss = parts[0].replace("跟进", "").replace(":", "").strip()
            st = parts[1].strip()
            if any(kw in st for kw in ("改善", "解决", "好转")):
                status = "improved"
            else:
                status = "unresolved"
            profile["diagnosed_issues"].append(
                {"issue": iss, "status": status, "date": today}
            )
            changed = True

        # case: "笔记: <自由文本>"
        elif "笔记" in line:
            n = line.replace("笔记", "").replace(":", "").strip()
            if n:
                profile["coach_notes"] = n
                changed = True

    if changed:
        profile_save(user_id, profile)

    return clean
