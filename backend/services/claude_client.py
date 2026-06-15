import json
import os
import re
from openai import OpenAI
from prompts.system_prompt import build_round1_prompt, build_roundn_prompt

_client = None
MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com"


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY environment variable not set")
        _client = OpenAI(api_key=api_key, base_url=BASE_URL, timeout=300.0)
    return _client


def _extract_json(text: str) -> dict | list:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from ```json ... ``` block
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        return json.loads(m.group(1))
    # Try finding the first [ or { and matching
    for start_char, end_char in [('[', ']'), ('{', '}')]:
        start = text.find(start_char)
        if start != -1:
            end = text.rfind(end_char)
            if end != -1:
                return json.loads(text[start:end + 1])
    raise ValueError(f"Could not extract JSON from LLM response: {text[:200]}...")


SCENARIO_LABELS = {"vibecoding": "Vibe Coding", "ppt": "PPT 制作"}


def generate_candidates(idea: str, scenario: str, custom_rules: str | None = None) -> list[dict]:
    """Generate 3 candidate prompts from a vague idea."""
    client = _get_client()
    label = SCENARIO_LABELS[scenario]
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=6144,
        messages=[
            {"role": "system", "content": build_round1_prompt(scenario, custom_rules)},
            {"role": "user", "content": f"请将以下模糊想法扩展为不同角度的{label}提示词：\n\n<idea>{idea}</idea>"}
        ]
    )
    text = resp.choices[0].message.content
    data = _extract_json(text)
    if isinstance(data, dict):
        data = [data]
    return data


def _parse_targeted_comments(comment: str, sentence_count: int) -> tuple[dict[int, str], str]:
    """
    逐行解析 comment 中的 @N 引用。
    每行以 @N 开头 → 行内剩余内容为该句的针对性意见。
    不以 @N 开头的行 → 全局意见。
    返回 ({0-based_index: comment_text}, global_comment)
    """
    if not comment:
        return {}, ""
    targeted: dict[int, str] = {}
    global_lines: list[str] = []
    for line in comment.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^@(\d+)\s+(.+)$', line)
        if m:
            idx = int(m.group(1)) - 1  # 1-based → 0-based
            content = m.group(2).strip()
            if 0 <= idx < sentence_count:
                if idx in targeted:
                    targeted[idx] += "；" + content
                else:
                    targeted[idx] = content
            else:
                # Invalid reference → demote to global
                global_lines.append(f"（对不存在的句子 @{m.group(1)} 的意见）{content}")
            continue
        m2 = re.match(r'^@(\d+)\s*$', line)
        if m2:
            # @N only, no content — ignore
            continue
        global_lines.append(line)
    global_comment = "\n".join(global_lines).strip()
    return targeted, global_comment


def _build_feedback_text(
    approved: list[str],
    rejected: list[str],
    unmarked: list[str],
    comment: str | None,
    sentences: list[dict] | None = None,
) -> str:
    """Build formatted feedback text from sentence-level votes and comment.

    Approved and unmarked sentences are referenced by number only (e.g. [1] [2] [3])
    to save tokens — their full text is already in the tasks/prompt section above.
    Rejected sentences retain full text for replacement context.
    """
    if sentences:
        approved_items = [(s["index"], s["text"]) for s in sentences if s.get("vote") == "approve"]
        rejected_items = [(s["index"], s["text"]) for s in sentences if s.get("vote") == "reject"]
        unmarked_items = [(s["index"], s["text"]) for s in sentences if s.get("vote") is None or s.get("vote") == "null"]
    else:
        approved_items = list(enumerate(approved))
        rejected_items = [(len(approved) + i, s) for i, s in enumerate(rejected)]
        unmarked_items = [(len(approved) + len(rejected) + i, s) for i, s in enumerate(unmarked)]

    sentence_count = len(approved_items) + len(rejected_items) + len(unmarked_items)
    targeted, global_comment = _parse_targeted_comments(comment or "", sentence_count)

    feedback_parts: list[str] = []

    # Approved sentences — number-only (LLM finds text in tasks/prompt above)
    if approved_items:
        nums = " ".join(f"[{idx + 1}]" for idx, _ in approved_items)
        feedback_parts.append(f"认可的句子（保留原文）：{nums}")
        # If an approved sentence has a targeted @N comment, include its text
        annotated = [(idx, text) for idx, text in approved_items if idx in targeted]
        if annotated:
            feedback_parts.append("  其中含针对性意见：")
            for idx, text in annotated:
                feedback_parts.append(f"  [{idx + 1}] {text}")
                feedback_parts.append(f"    用户针对此句的意见：{targeted.pop(idx)}")

    # Rejected sentences — keep full text (needed for replacement)
    if rejected_items:
        if feedback_parts:
            feedback_parts.append("")
        feedback_parts.append("反对的句子：")
        for idx, text in rejected_items:
            label = f"- [{idx + 1}] {text}"
            if idx in targeted:
                label += f"\n  用户针对此句的意见：{targeted.pop(idx)}"
            feedback_parts.append(label)

    # Unmarked sentences — number-only
    if unmarked_items:
        if feedback_parts:
            feedback_parts.append("")
        nums = " ".join(f"[{idx + 1}]" for idx, _ in unmarked_items)
        feedback_parts.append(f"未标注的句子（可酌情调整）：{nums}")
        annotated = [(idx, text) for idx, text in unmarked_items if idx in targeted]
        if annotated:
            feedback_parts.append("  其中含针对性意见：")
            for idx, text in annotated:
                feedback_parts.append(f"  [{idx + 1}] {text}")
                feedback_parts.append(f"    用户针对此句的意见：{targeted.pop(idx)}")

    leftover = [f"（对句子 @{idx + 1}）{txt}" for idx, txt in sorted(targeted.items())]
    if leftover:
        global_comment = global_comment + "\n" + "\n".join(leftover) if global_comment else "\n".join(leftover)
        global_comment = global_comment.strip()

    if global_comment:
        if feedback_parts:
            feedback_parts.append("")
        feedback_parts.append(f"用户全局意见：{global_comment}")

    return "\n".join(feedback_parts)


def refine_prompt(
    current_prompt: str,
    approved: list[str],
    rejected: list[str],
    unmarked: list[str],
    comment: str | None,
    scenario: str,
    blueprint: str | None = None,
    tasks: list[dict] | None = None,
    sentences: list[dict] | None = None,
) -> dict:
    """Refine based on sentence-level feedback. Returns dict with 'prompt' (PPT) or 'blueprint'+'tasks' (vibecoding)."""
    client = _get_client()
    feedback_text = _build_feedback_text(approved, rejected, unmarked, comment, sentences)

    if scenario == "vibecoding" and blueprint and tasks:
        tasks_text = "\n".join(
            f"Task {t['id']}: {t['title']}\n{t['prompt']}" for t in tasks
        )
        user_msg = f"""以下是当前的项目计划和用户的反馈。请根据反馈精炼。

<blueprint>{blueprint}</blueprint>

<tasks>
{tasks_text}
</tasks>

<feedback>
{feedback_text}
</feedback>

（反馈中以 [N] 引用的句子，原文在上方 tasks 中按先后顺序查找。反馈格式说明：\"认可的句子\"和\"未标注的句子\"仅列序号以节省篇幅；\"反对的句子\"附有原文以便替换。）

请输出精炼后的 blueprint 和 tasks。"""
    else:
        user_msg = f"""以下是上一轮生成的提示词和用户的逐句反馈。请根据反馈精炼提示词。

<current_prompt>{current_prompt}</current_prompt>

<feedback>
{feedback_text}
</feedback>

（反馈中以 [N] 引用的句子，原文在上方 current_prompt 中按先后顺序查找。反馈格式说明：\"认可的句子\"和\"未标注的句子\"仅列序号以节省篇幅；\"反对的句子\"附有原文以便替换。）

请生成精炼后的提示词。"""

    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=6144,
        messages=[
            {"role": "system", "content": build_roundn_prompt(scenario)},
            {"role": "user", "content": user_msg}
        ]
    )
    text = resp.choices[0].message.content
    return _extract_json(text)
