"""
OW Coach — Pure LLM conversation agent.
No data APIs, no scoring, no external dependencies.
"""

import json, os, sys
from . import memory as mem
from .hero_db.lookup import detect_heroes, get_hero_info_text
from .hero_db.fandom import get_hero_strategy, get_hero_overview

PROMPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")


def read(name: str) -> str:
    p = os.path.join(PROMPTS, name)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def _collect_hero_context(history: list[dict], user_input: str = "") -> str | None:
    """扫描对话中提到的英雄，返回技能 + 数值 + 版本变动 + 策略文本。"""
    import json

    all_text = user_input
    for m in history:
        all_text += "\n" + m.get("content", "")
    hero_ids = detect_heroes(all_text)
    if not hero_ids:
        return None

    stats_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hero_db", "stats_cache")

    blocks = []
    seen = set()
    # 最多注入 3 个英雄的策略文本（token 控制）
    for hid in hero_ids[:3]:
        if hid in seen:
            continue
        seen.add(hid)

        # 技能数据（来自 data.py）
        info = get_hero_info_text(hid)
        if not info:
            continue

        # 定位描述（来自 Fandom overview）
        try:
            overview = get_hero_overview(hid)
            if overview:
                info += f"\n定位: {overview[:200]}"
        except Exception:
            pass  # Fandom API 不可用时跳过

        # 数值字段（来自 overlab.cn 页面解析）
        stats_path = os.path.join(stats_dir, f"{hid}_stats.json")
        if os.path.exists(stats_path):
            with open(stats_path, encoding="utf-8") as f:
                stats_data = json.load(f)
            stat_lines = ["\n\n数值数据:"]
            for skill_key, fields in stats_data.items():
                if skill_key.startswith("_"):
                    continue
                skill_name = fields.pop("_skill_name", skill_key)
                stat_lines.append(f"  [{skill_name}]")
                for label, val in fields.items():
                    if label in ("_skill_name",):
                        continue
                    stat_lines.append(f"    {label}: {val}")
                fields["_skill_name"] = skill_name  # restore
            if len(stat_lines) > 1:
                info += "\n".join(stat_lines)

        # 已移除内容 / 版本变动
        removed_path = os.path.join(stats_dir, f"{hid}_removed.json")
        if os.path.exists(removed_path):
            with open(removed_path, encoding="utf-8") as f:
                removed_data = json.load(f)
            if removed_data:
                info += "\n\n版本变动（已移除/变为基础技能的内容）:"
                for item in removed_data:
                    season = item.get("season", "") or ""
                    note = item.get("note", "") or ""
                    info += f"\n  - [{item.get('name','')}]{' ('+season+')' if season else ''}: {note[:120]}"

        # 策略文本（来自 Fandom wiki 社区策略库）
        try:
            strat = get_hero_strategy(hid)
            if strat:
                cleaned = strat.replace("This section is a stub section.", "").strip()
                trimmed = cleaned[:800]
                info += f"\n\n战术要点（来自社区策略库）:\n{trimmed}"
        except Exception:
            pass

        blocks.append(info)

    return "\n\n".join(blocks) if blocks else None


def build_prompt(user_id: str, history: list[dict], user_input: str = "") -> str:
    """Assemble the full multi-layer system prompt."""
    layers = [
        read("system.md"),
        read("framework.md"),
        read("knowledge.md"),
    ]

    # Layer 4 — Player profile (cross-session memory)
    profile = mem.profile_load(user_id)
    has_issues = bool(profile["diagnosed_issues"])
    has_solutions = bool(profile["solutions_provided"])
    has_notes = bool(profile["coach_notes"])

    if has_issues or has_solutions or has_notes:
        parts = [
            "## 玩家档案（跨对话记忆）",
            "以下是你对这位玩家已有的了解。参考但不完全依赖——玩家可能已经在进步。",
        ]

        if has_issues:
            lines = ["\n### 历史诊断的痛点"]
            for iss in profile["diagnosed_issues"][-8:]:
                if iss["status"] == "improved":
                    tag = "[已改善]"
                elif iss["status"] == "unresolved":
                    tag = "[未解决]"
                else:
                    tag = "[诊断]"
                lines.append(f"- {tag} {iss['issue']}")
            parts.append("\n".join(lines))

        if has_solutions:
            lines = ["\n### 过往给出的方案"]
            for sol in profile["solutions_provided"][-8:]:
                lines.append(f"- {sol['solution']}")
            parts.append("\n".join(lines))

        if has_notes:
            parts.append(f"\n### 教练笔记\n{profile['coach_notes']}")

        layers.append("\n\n".join(parts))

    # Layer 5 — Hero knowledge (auto-detected from conversation)
    hero_ctx = _collect_hero_context(history, user_input)
    if hero_ctx:
        layers.append(f"## 英雄档案（知识库）\n\n{hero_ctx}")

    # Layer 6 — Recent conversation history (last 10 exchanges)
    if history:
        recent = history[-10:]
        ctx = "\n".join(
            f"{'玩家' if m['role']=='user' else '教练'}: {m['content'][:200]}"
            for m in recent
        )
        layers.append(f"## 近期对话\n\n{ctx}")

    return "\n\n---\n\n".join(layers)


def respond(
    user_id: str,
    user_input: str,
    llm_callback=None,
) -> str:
    """
    Full coach response cycle.

    Args:
        user_id: Any identifier (Discord ID, session ID, etc.)
        user_input: The player's message
        llm_callback: Optional callable(system_prompt, history, user_input) -> str.
                      If None, returns assembled system prompt for inspection.

    Returns:
        Coach's response text (cleaned, with [档案] section stripped).
    """
    history = mem.load(user_id)
    system = build_prompt(user_id, history, user_input)

    if llm_callback is None:
        return system

    response = llm_callback(system, history, user_input)

    # Extract and persist [档案] section before saving to history
    response = mem.profile_apply_updates(user_id, response)

    mem.add(user_id, user_input, response)
    return response


def cli():
    print("=" * 55)
    print("  OW Coach — 交互测试 (纯 LLM 对话)")
    print("  输入 'exit' 退出 / 'prompt' 查看完整提示词")
    print("  输入 'profile' 查看当前玩家档案")
    print("=" * 55)
    uid = "cli_user"

    while True:
        try:
            text = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text.lower() == "exit":
            break
        if text.lower() == "prompt":
            h = mem.load(uid)
            print(build_prompt(uid, h))
            continue
        if text.lower() == "profile":
            p = mem.profile_load(uid)
            print(json.dumps(p, ensure_ascii=False, indent=2))
            continue

        prompt = respond(uid, text)
        print(f"\n[Assembled System Prompt — no LLM connected]\n{'='*40}")
        print(prompt[:1500])


if __name__ == "__main__":
    cli()
