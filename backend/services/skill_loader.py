"""Skill file loader — reads quality-standard skill files from disk.

Directory layout:
  prompts/skills/
    builtin/       # shipped with the app, read-only
      clean_code.txt
      react.txt
      typescript.txt
      fullstack.txt
    custom/        # user-created at runtime via API
      *.txt

Each file is plain text.  Builtin skill names come from BUILTIN_NAMES.
Custom skill files may start with a "# Name" comment on the first line;
otherwise the filename stem is used as the display name.
"""

from __future__ import annotations

import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "skills"
BUILTIN_DIR = SKILLS_DIR / "builtin"
CUSTOM_DIR = SKILLS_DIR / "custom"

BUILTIN_NAMES: dict[str, str] = {
    "clean_code": "默认 Clean Code 规范",
    "react": "React 最佳实践",
    "typescript": "TypeScript 严格模式",
    "fullstack": "全栈项目规范",
}

BUILTIN_ORDER: list[str] = ["clean_code", "react", "typescript", "fullstack"]

MAX_CUSTOM_SKILLS = 10


# ── public API ───────────────────────────────────────────────────────

def load_all_skills() -> list[dict]:
    """Return every available skill as a list of dicts.

    Each dict: ``{id, name, preview, content, is_custom}``.
    Builtin skills come first in ``BUILTIN_ORDER``; custom skills are
    sorted by file modification time (oldest first).
    """
    skills: list[dict] = []

    # builtin
    for sid in BUILTIN_ORDER:
        filepath = BUILTIN_DIR / f"{sid}.txt"
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8").strip()
        name = BUILTIN_NAMES.get(sid, sid)
        skills.append(_skill_dict(sid, name, content, is_custom=False))

    # custom
    if CUSTOM_DIR.exists():
        custom_files = sorted(
            CUSTOM_DIR.glob("*.txt"), key=lambda p: p.stat().st_mtime
        )
        for filepath in custom_files:
            content = filepath.read_text(encoding="utf-8").strip()
            if not content:
                continue
            sid = filepath.stem
            name = _extract_name(content) if content.startswith("#") else sid
            skills.append(_skill_dict(sid, name, content, is_custom=True))

    return skills


def get_skill_content(skill_id: str) -> str | None:
    """Read the full text of a skill by its id.  Returns *None* when the
    id is unsafe or the file does not exist."""
    if _unsafe(skill_id):
        return None

    for base in (BUILTIN_DIR, CUSTOM_DIR):
        filepath = base / f"{skill_id}.txt"
        if filepath.exists():
            return filepath.read_text(encoding="utf-8").strip()
    return None


def save_custom_skill(name: str, content: str) -> dict:
    """Persist a user-created skill and return ``{id, name, content}``.

    The file is written to ``custom/<slug>.txt``.  The display *name* is
    stored as a ``# Name`` comment on the first line so ``load_all_skills``
    can recover it."""
    _ensure_custom_dir()

    if count_custom_skills() >= MAX_CUSTOM_SKILLS:
        raise ValueError(f"最多只能保存 {MAX_CUSTOM_SKILLS} 个自定义技能")

    skill_id = _slugify(name)

    # wire the display name into the file itself
    body = f"# {name}\n{content}"

    filepath = CUSTOM_DIR / f"{skill_id}.txt"
    filepath.write_text(body, encoding="utf-8")

    return {"id": skill_id, "name": name, "content": content}


def delete_custom_skill(skill_id: str) -> bool:
    """Delete a custom skill file.  Builtin skills cannot be deleted.
    Returns *True* if the file was removed, *False* otherwise."""
    if _unsafe(skill_id):
        return False

    # never delete builtin skills
    if (BUILTIN_DIR / f"{skill_id}.txt").exists():
        return False

    filepath = CUSTOM_DIR / f"{skill_id}.txt"
    if filepath.exists():
        filepath.unlink()
        return True
    return False


def count_custom_skills() -> int:
    """Return the number of custom skill files on disk."""
    if not CUSTOM_DIR.exists():
        return 0
    return len(list(CUSTOM_DIR.glob("*.txt")))


# ── internal helpers ─────────────────────────────────────────────────

def _skill_dict(sid: str, name: str, content: str, *, is_custom: bool) -> dict:
    preview = content if len(content) <= 80 else content[:80] + "…"
    # skip the "# Name" comment line for custom skills when returning content
    display_content = content
    if is_custom and content.startswith("#"):
        # strip the first line (name comment) for the API response
        lines = content.split("\n", 1)
        display_content = lines[1].strip() if len(lines) > 1 else ""
    return {
        "id": sid,
        "name": name,
        "preview": preview if len(preview) <= 80 else preview[:80] + "…",
        "content": display_content,
        "is_custom": is_custom,
    }


def _extract_name(content: str) -> str:
    """Pull the display name from a ``# Name`` first-line comment."""
    first_line = content.split("\n", 1)[0]
    return first_line.lstrip("#").strip() or "未命名"


def _slugify(name: str) -> str:
    """Turn a user-provided display name into a filesystem-safe id."""
    # keep alphanumeric, Chinese characters, underscores; collapse runs
    safe = re.sub(r"[^\w一-鿿]+", "_", name).strip("_")[:50]
    if not safe:
        safe = "custom_skill"

    # ensure uniqueness
    sid = safe
    n = 1
    while (CUSTOM_DIR / f"{sid}.txt").exists():
        n += 1
        sid = f"{safe}_{n}"
    return sid


def _unsafe(skill_id: str) -> bool:
    return ".." in skill_id or "/" in skill_id or "\\" in skill_id


def _ensure_custom_dir() -> None:
    CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
