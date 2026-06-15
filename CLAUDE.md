# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

UPFLIP (User Preference Feedback Loop Improver for Prompts) — a standalone web app that refines vague prompts into precise ones. It supports two vertical scenarios: **Vibe Coding** (AI-assisted coding prompts with blueprint + task breakdown) and **PPT制作** (presentation creation prompts). For Vibe Coding, the output is a project blueprint + summary + independently executable task prompts — not a single giant prompt. The user enters a fuzzy idea, the backend calls DeepSeek API to generate 1–3 candidate plans from different angles, the user picks one and annotates sentences or tasks, and after refinement (or immediate finalization) gets a polished output.

## Architecture

```
Browser (index.html)  ←→  FastAPI backend (Python)  ←→  DeepSeek API (via OpenAI SDK)
     static/                 routes/ + services/
```

- **Backend**: Python + FastAPI, no database (in-memory `store.py` keyed by session UUID)
- **Frontend**: Single HTML file (`backend/static/index.html`) served as static asset. Contains both the landing page and the full app SPA in one file.
- **LLM**: DeepSeek (`deepseek-chat`) via OpenAI SDK, not Anthropic
- **Prompt intelligence**: Scenario-specific skill models + builder functions in `backend/prompts/system_prompt.py`

## Running the app

```bash
# .env must contain DEEPSEEK_API_KEY (not ANTHROPIC_API_KEY)
# DEEPSEEK_API_KEY=sk-...

pip install -r backend/requirements.txt

# Must set PYTHONPATH so imports resolve; python is at D:/anaconda/python.exe
PYTHONPATH="backend" uvicorn backend.main:app --reload --port 8080
```

On Windows PowerShell:
```powershell
$env:PYTHONPATH="backend"; D:/anaconda/python.exe -m uvicorn backend.main:app --reload --port 8080
```

No build step. `uvicorn` serves both the API and the static frontend from `/`.

Before restarting, kill the old process:
```powershell
Get-NetTCPConnection -LocalPort 8080 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

## Landing page architecture

The landing page (`#landingWrapper`) sits above the app (`#appContainer`) and uses z-ordering with `display: none/block` toggling. It has four layers:

```
landing-wrapper (absolute, full viewport)
  ├── landing-bg (fixed, full viewport)
  │     ├── <video> bg.mp4 (muted autoplay loop)
  │     ├── .landing-overlay (gradient: white 90%→75%→0% left-to-right)
  │     ├── .wm-cover-tl (top-left watermark cover, HSL-matched to video)
  │     └── .wm-cover-br (bottom-right watermark cover)
  ├── .top-nav-wrapper (absolute, top:24px, left:90px, right:40px)
  │     └── .top-nav (frosted glass: rgba(255,255,255,0.32) + blur(10px))
  │           ├── .top-nav-bar (hamburger + UPFLIP logo + 登录 button)
  │           └── .top-nav-content (3 dark cards, CSS height transition)
  └── .landing-content (absolute, left:90px, top:160px, bottom:180px)
        ├── .landing-brand "UPFLIP" (26px, #F5A623)
        ├── .landing-title (88px, character-by-character blur-in)
        ├── .landing-subtitle (22px, word-by-word blur-in)
        └── .scenario-selection (flex-column, gap:12px, max-width:460px, margin-top:auto)
              ├── .sc-card (Vibe Coding — computer SVG icon)
              └── .sc-card (PPT制作 — slides SVG icon)
```

### Landing page key behaviors

- **Video background**: `bg.mp4` in `backend/static/` (copied from source video). Source: `<source src="/bg.mp4">` — FastAPI serves static at `/`, not `/static/`.
- **Watermark covers**: Two absolutely-positioned `<div>` elements with `::before` (HSL-matched gradient) and `::after` (SVG feTurbulence noise texture) to hide watermarks on the source video. Calibrated via HSL color space: top-left at H245/S10%/L98%→96%, bottom-right at H245/S15%/L90%→88%. Soft edges via box-shadow spread/blur (60px/36px for top-left).
- **Top nav**: Frosted glass effect (`backdrop-filter: blur(10px)`, `rgba(255,255,255,0.32)`). Hamburger menu toggles `.open` class via JS — nav expands from 64px to 230px with CSS `height` transition. Three inner cards have dark backgrounds (`#1B1722` / `#2F293A`) with white text. Click outside closes the nav. Mobile responsive: cards stack vertically, expanded height 360px.
- **Scenario cards**: Minimalist white cards (`#ffffff`, border-radius 18px, `1px solid rgba(0,0,0,0.05)`, subtle shadow). Hover: `translateY(-3px)` + 6-layer amber-to-lavender box-shadow glow (12px→130px spread, warm iridescent). SVG icons in 48px `#eaecf0` circles, hover scale 1.05. Right arrow `›` moves 6px on hover. Selected state: darker border + shadow.
- **Blur-in animation**: `@keyframes blurIn` (blur 10px→0, opacity 0→1, translateY -30→0). Title split into `<span class="char">` with 40ms stagger. Subtitle split into `<span class="word">` with 100ms stagger + 300ms initial delay. Pure CSS + vanilla JS, no library dependency.

### Responsive breakpoints

| Breakpoint | Changes |
|------------|---------|
| `max-width: 900px` | Content left 40px, title 56px, scenario-selection max-width 400px |
| `max-width: 600px` | Content relative positioning, title 36px normal wrap, nav margins 20px, cards full-width, overlay full coverage, candidate cards stack vertically, selection header left-aligns |

## Video backgrounds

Two independent full-viewport video layers, toggled by JS:

| Video | File | Element | When visible |
|-------|------|---------|--------------|
| Landing page | `backend/static/bg.mp4` | `.landing-bg` (id `landingBg`) | Landing page shown |
| App pages | `backend/static/app_bg.mp4` | `.app-bg` (id `appBg`) | Scenario selected, app visible |

Both use `position: fixed; inset: 0; z-index: 0` with `<video autoplay muted loop playsinline>` and `object-fit: cover`. `selectScenario()` hides landing-bg and shows appBg. `restart()` (return to landing) does the reverse.

## App hero area structure

The app hero section (`.hero-input`, initially `display:none`, toggled via `.visible`) is vertically centered at `padding: 120px 24px 40px`. It stacks these elements:

```
.hero-input (flex-column, align-items:center, gap:34px)
  ├── .hero-badge-wrapper (white pill: bg #fff, border-radius 24px, subtle shadow)
  │     ├── .hero-badge (dark "★ New" badge, bg #1B1722, border-radius 20px, z-index:1 floating)
  │     └── .hero-badge-label (scenario name: "Vibe Coding" / "PPT制作", color #292524)
  ├── .hero-title "UPFLIP" (80px, Fustat 800, #fff with text-shadow)
  ├── .hero-subtitle (20px, Fustat 500, rgba(255,255,255,0.8))
  └── .search-box (frosted glass: rgba(0,0,0,0.20) + blur(24px), border-radius 22px)
        ├── .sb-top (transparent header row: skill label + "Powered by DeepSeek" badge)
        └── .sb-body (white card: bg #fff, border-radius 14px, floating on glass)
              ├── .sb-input-row (textarea + submit button, padding 18px)
              └── .sb-bottom (skill dropdown select + char count, padding 0 18px 16px)
```

**Key behaviors:**
- `.hero-badge-wrapper` — white pill wrapping the dark badge. The badge gets `position: relative; z-index: 1` to appear floating. The label text is updated by `selectScenario()` via the `heroBadgeLabel` DOM ref.
- `.search-box` — frosted glass background layer with `overflow: visible` (critical: `backdrop-filter` creates a stacking context that would otherwise clip the `<select>` dropdown).
- `.sb-body` — white card floating on the glass, contains the actual input area. All inner elements inherit the white background.
- `.sb-top` — transparent row inside the glass; only the `.sb-skill-label` (pill) and `.sb-ai-badge` text render with light colors (`rgba(255,255,255,0.8)`).
- Skill dropdown (`#heroSkillSelect`) — visible only for Vibe Coding scenario. Contains a `<select>` with options: default Clean Code, React, TypeScript, fullstack, custom. Styled with `background: #f5f5f4` and `color: #292524` matching the white card theme. `<option>` elements explicitly set `background: #ffffff; color: #292524` to override browser defaults.

## App container

`.app-container` is `max-width: 720px; margin: 0 auto; padding: 40px 24px; background: #ffffff; min-height: 100vh; position: relative; z-index: 1`. The `z-index: 1` is essential — without it, the fixed video background (`z-index: 0`) paints above the static container.

During hero mode (no session active), `.app-container.hero-mode` sets `background: transparent; max-width: none; margin: 0; min-height: 100vh; padding: 0` so the video background shows through.

## Key files

| File | Role |
|------|------|
| `backend/main.py` | FastAPI app, CORS, static file mount at `/` |
| `backend/routes/optimize.py` | 4 API endpoints (session CRUD + feedback + finalize). Finalize is read-only (no API call). |
| `backend/services/claude_client.py` | DeepSeek API wrapper — `generate_candidates()`, `refine_prompt()`, `_build_feedback_text()`, `_parse_targeted_comments()`, `_extract_json()` |
| `backend/services/optimizer.py` | Core protocol: session lifecycle, feedback processing, convergence detection, early finalize |
| `backend/store.py` | In-memory `SessionStore` dict with `SessionState` objects |
| `backend/models/schemas.py` | Pydantic models: `TaskItem`, `CandidateOut`, `SessionOut`, `CreateSessionRequest`, `FeedbackRequest` (`SentenceFeedback` with index/text/vote), `FinalizeResponse` |
| `backend/prompts/system_prompt.py` | Scenario skill models (`VIBECODING_SKILL`, `PPT_SKILL`), round 1 / round N templates. `build_round1_prompt()` builds the full system prompt (skill model + quality section + protocol). `build_roundn_prompt()` is a one-liner: `return _ROUNDN_VIBECODING if scenario == "vibecoding" else _ROUNDN_PPT` — no skill model injection, no placeholders. |
| `backend/static/index.html` | Complete frontend SPA — scenario selection, candidate cards, task review (vibecoding) or prompt annotation (PPT), @N comment support, final output |

## Two scenarios

The app focuses exclusively on two verticals, selected at startup via card UI:

| Scenario | `scenario` key | Output format | Annotation target |
|----------|---------------|---------------|-------------------|
| Vibe Coding | `vibecoding` | `{blueprint, summary, tasks: [{id, title, prompt}]}` | Per-task sentences |
| PPT制作 | `ppt` | `{prompt}` (flowing prose) | Prompt sentences |

The scenario persists in session state via URL hash. A scenario pill is visible throughout.

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/sessions` | Create session — `CreateSessionRequest` includes `idea`, `scenario` (`vibecoding`\|`ppt`), optional `custom_rules`. DeepSeek generates 1–3 candidates, returns `SessionOut` |
| `GET` | `/api/sessions/{id}` | Restore session state (enables page refresh via URL hash `#<id>`) |
| `POST` | `/api/sessions/{id}/feedback` | Submit `selected_candidate`, `sentences` (with per-sentence votes), optional `comment`. DeepSeek refines. Returns updated `SessionOut` |
| `POST` | `/api/sessions/{id}/finalize` | Return `FinalizeResponse` — read-only, no API call |
| `GET` | `/api/health` | Health check |

## Session lifecycle

1. **Create**: `POST /api/sessions` → `store.create()` → `generate_candidates()` via DeepSeek → return `SessionOut` (phase: `"selection"`, 1–3 candidates)
2. **Feedback** (repeatable): `POST /api/sessions/{id}/feedback` →
   - If round 1 + phase "selection": records chosen angle + content. For vibecoding, stores `blueprint`, `summary`, `tasks`; for PPT, stores `current_prompt`. Switches phase to `"refinement"`.
   - **Early finalize**: If this is the first feedback AND no sentences were annotated AND no comment → skips DeepSeek refinement entirely (returns immediately). The frontend "直接定稿" button sends an empty feedback to commit the selection, then calls finalize.
   - Otherwise: calls `refine_prompt()` via DeepSeek → updates blueprint/tasks (vibecoding) or prompt (PPT) → increment round → check convergence.
3. **Convergence**: fires when round ≥ 3, rejected sentences ≤ 1, comment empty/short (<20 chars). Frontend shows convergence bar with "定稿" and "继续精炼" buttons.
4. **Finalize**: `POST /api/sessions/{id}/finalize` → returns final output. This endpoint makes no API call — it just reads the current session state.

## Round 1 vs Round N prompt design

The system prompts for generation and refinement serve fundamentally different purposes:

| Aspect | Round 1 (`generate_candidates`) | Round N (`refine_prompt`) |
|--------|------|------|
| **Role** | Divergent generation — vague idea → 1–3 distinct plans | Convergent refinement — current plan + feedback → one improved plan |
| **System prompt** | Full skill model (`VIBECODING_SKILL`/`PPT_SKILL`) + quality section + protocol (~5000 chars) | Refinement protocol only (~2200 chars) — no skill model |
| **Input** | Just `<idea>raw text</idea>` | `<blueprint>`, `<tasks>`, `<feedback>` — full current state |
| **Output** | JSON **array** of candidates (each with `angle`, `description`) | JSON **object** — single refined plan |
| **`session.round`** | Always 1 (generation happens at session creation) | ≥ 2 (incremented at each `process_feedback`) |

**Why Round N excludes the skill model:** The engineering quality standards (SOLID, DRY, type safety, etc.) are baked into the output during Round 1. Re-injecting them in Round N would cause "quality creep" — the LLM adding new requirements each round instead of surgically applying user feedback. The Round N guardrails say "quality must not be stripped away" (defensive) rather than re-teaching the full skill model.

**User message structure for Round N** (vibecoding):
```
<blueprint>...</blueprint>
<tasks>Task 1: title\nprompt text\n...</tasks>
<feedback>认可的句子：[1] [2] [4]\n反对的句子：\n- [3] text\n  用户意见：...</feedback>
（格式说明：序号句子在上方 tasks 中交叉引用查找原文）
```

## @N targeted comment system

Users can target specific sentences with feedback in the comment textarea using `@N` notation:

- Each line starting with `@N content` targets sentence N (1-based, matching the number badge shown in the UI)
- Lines without `@N` are treated as global comments
- `@N` on a line by itself (no content) is ignored
- Multiple references to the same sentence are merged with `；`
- References to non-existent sentence numbers are demoted to global comments

Parsing is handled by `_parse_targeted_comments(comment, sentence_count)` in `claude_client.py`, which returns `({0-based_index: comment_text}, global_comment)`.

**Feedback text format** (built by `_build_feedback_text`):
- **Approved sentences**: number-only — `认可的句子（保留原文）：[1] [2] [4] [5]` (LLM cross-references full text from `<tasks>`)
- **Rejected sentences**: full text retained — `- [3] Use GraphQL with Apollo.\n  用户针对此句的意见：改用 REST` (needs context for replacement)
- **Unmarked sentences**: number-only — `未标注的句子（可酌情调整）：[6] [7]`
- **Targeted comments** marked as `"用户针对此句的意见"`; global comments as `"用户全局意见"`
- **Edge case**: if an approved/unmarked sentence has a targeted `@N` comment, its text is expanded inline under `"其中含针对性意见"` subsection

This format cuts feedback text tokens by ~52% compared to listing every sentence's full text.

Sentence number badges are rendered inside the colored feedback span: `<span class="sentence approve"><span class="sentence-num">1</span>text</span>`. Global indices across tasks are pre-computed by `computeGlobalIndices()` in the frontend.

**Index convention**: `SentenceFeedback.index` is **0-based** in the backend. All UI rendering (`@N` in comments, sentence badges, feedback labels) uses **1-based** display. `_parse_targeted_comments()` converts `@N` (1-based) → `idx - 1` (0-based internal). `_build_feedback_text()` converts back: `[idx + 1]` (1-based display).

## Vibe Coding output structure

Candidates and refined output use the blueprint + task breakdown format:

```json
{
  "id": 1,
  "angle": "自底向上逐步构建",
  "description": "从数据模型开始，逐层向上构建 UI",
  "blueprint": "技术栈：Next.js + Prisma + SQLite。目录结构：...",
  "summary": "这是一个博客系统，用户输入文章后系统会自动发布并展示...",
  "tasks": [
    {"id": 1, "title": "项目脚手架与基础配置", "prompt": "You are a senior..."},
    {"id": 2, "title": "文章数据模型与 API", "prompt": "..."}
  ]
}
```

- **blueprint**: 3-5 sentences, Chinese with English technical terms. Tech stack, directory structure, data models, architectural decisions.
- **summary**: 2-4 plain Chinese sentences for non-technical users — what goes in, what comes out, main features.
- **tasks**: 3-5 independently executable task prompts. Each is 4-7 sentences, self-contained, paste-ready. Ordered by dependency: scaffolding → data layer → core features → polish.

## Custom rules

Both scenarios support custom quality/style rules, but the UI differs:

- **Vibe Coding**: A `<select>` dropdown (`#heroSkillDropdown`) in the search box offers presets: default Clean Code, React best practices, TypeScript strict, fullstack, or custom. Selecting a preset passes its key as `custom_rules`. Choosing "default" passes `null` (uses `DEFAULT_QUALITY_SECTION` — SOLID, DRY, type safety, error handling, observability). The dropdown is only visible when Vibe Coding is the active scenario.
- **PPT**: A collapsible textarea (`#customRulesInput`) below the input area. Empty = use built-in `PPT_SKILL`.

The `custom_rules` value is stored in session state and passed to `build_round1_prompt()`. For vibecoding, it replaces the `{quality_section}` placeholder in `VIBECODING_SKILL`. For PPT, it's currently stored but the PPT round 1 template does not use a quality placeholder.

## Angle selection design

The system prompt's Protocol Step 2 does NOT give the LLM a fixed list of angle names to pick from. Instead, it instructs the LLM to analyze the user's specific idea and derive 1–3 genuinely different approaches from that analysis. If an idea has only one natural architecture (or rhetorical strategy for PPT), outputting one plan is acceptable — the LLM is told not to pad to 3 just because. This keeps angles specific to each request rather than recycling generic labels.

## Frontend edge cases

- Vibe Coding cards gracefully handle a missing `blueprint` field (DeepSeek occasionally omits it) by falling back to show `description` + task count instead of an empty card.
- "直接定稿" button behavior depends on phase: in `"selection"` phase it first calls feedback (to commit the candidate choice, backend skips DeepSeek via early-finalize path) then finalize; in `"refinement"` phase it skips feedback entirely and calls finalize directly (no unnecessary API call).

## Frontend flow

0. **Landing page** — Video background with frosted-glass top nav (UPFLIP logo + hamburger menu + 登录 button). Two minimalist scenario cards (Vibe Coding with computer icon, PPT制作 with slides icon). Blur-in text animation on load. Selecting a scenario hides the landing wrapper and shows the app.

1. **Input** — textarea (`#heroIdeaInput`) with scenario-appropriate placeholder. Vibe Coding shows a skill preset dropdown in the search box (`.sb-bottom`); PPT shows nothing in that slot. Character counter at `0/3,000`. Submit button → `POST /api/sessions`.
2. **Selection** — 1–3 candidate cards displayed horizontally (`#candidatesList` is `display: flex; justify-content: center; gap: 20px; flex-wrap: wrap`). Cards are `flex: 1 1 300px; min-width: 260px; max-width: 400px` — equal-width, side-by-side. For vibecoding: shows blueprint excerpt + task count badge. For PPT: shows full prompt text. User clicks to select, card gets `.selected` class (teal border + ring). At ≤600px, cards stack vertically. Header `.selection-header` is centered above the cards.
3. **Task review** (vibecoding) — blueprint box at top with summary section below. Task cards in accordion: click header to expand, each task's prompt is split into sentences for left-click=approve / right-click=reject. Per-task ✓保留/✗删除 vote buttons. Sentences are globally numbered across all tasks via `computeGlobalIndices()`.
4. **Annotation** (PPT) — prompt text split into sentences, left-click=approve, right-click=reject, click again=clear.
5. **Actions** — "提交反馈" (refine via DeepSeek), "直接定稿" (finalize, skips API call in refinement phase), "重置所有标注". Comment textarea supports `@N` notation for targeted feedback.
6. **Final** — For vibecoding: blueprint + summary + task cards with per-task copy buttons + "复制全部" button. For PPT: prompt text with copy button.

Session ID persists in URL hash (`#<id>`) for refresh recovery. A "返回首页" link lets users go back to the landing page (shows `#landingWrapper`, hides `#appContainer`).

### Landing → app transition

- `#landingWrapper` and `#appContainer` are mutually exclusive via `.visible` class (toggles `display: none/block`).
- Scenario selection calls `selectScenario(key)` which hides the landing, shows the app, and updates the scenario pill.
- URL hash `#<sessionId>` on the app page triggers session restore via `GET /api/sessions/{id}`.

## Design constraints

- Session state is in-memory only — restarting the server loses all sessions
- DeepSeek API via OpenAI SDK: `deepseek-chat`, max_tokens 6144, timeout 300s
- JSON extraction uses `_extract_json()` with markdown code block + fallback bracket matching (DeepSeek sometimes wraps JSON in ```json```)
- All UI text is Chinese (zh-CN)
- Sentence-splitting normalizes whitespace: `text.replace(/\s+/g, ' ')`. `.` is only treated as a sentence terminator when followed by whitespace or end-of-string (`\.(?=\s|$)`), so filenames like `main.ts` and `schema.prisma` don't get split.
- Per-task sentence annotation uses event delegation on `#taskList` (dynamic content)
- The system python is at `D:/anaconda/python.exe` (Windows `python` alias may resolve to WindowsApps stub)
- The landing page video (`bg.mp4`) is served from `/bg.mp4` (FastAPI static mount at `/`, not `/static/`). The app page video is at `/app_bg.mp4`.
- Watermark covers use HSL color space for precise background matching; adjustments should stay in H245 ±5 hue range
- Top nav is positioned at `left:90px; right:40px` (aligned with title text on the left, fluid width)
- **`backdrop-filter` clipping caveat**: `backdrop-filter: blur()` creates a stacking context that clips child elements. `.search-box` must have `overflow: visible` so the skill `<select>` dropdown isn't hidden. Similarly, ancestor elements with `overflow: hidden` will break the blur effect.
