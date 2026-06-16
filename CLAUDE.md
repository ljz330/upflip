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
- **Skill system**: File-based quality-standard presets in `backend/prompts/skills/builtin/` and `custom/`, loaded by `backend/services/skill_loader.py`

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

## Color scheme

The app uses a warm orange accent palette. The brand color is `#F5A623`.

| Token | Value | Usage |
|-------|-------|-------|
| Brand orange | `#F5A623` | Primary buttons, focus rings, selected states, card accents, spinner |
| Dark orange | `#D4951E` / `#B87A1E` | Button hover, heading text on white |
| Orange tint | `#fff8f0` / `#fff5f0` | Light backgrounds (convergence bar, card badges, drag-over) |
| Warm border | `#fef3c7` | Subtle orange borders (scenario pills) |

The three candidate cards use distinct orange tones: card-1 `#F5A623`, card-2 `#E8734A` (burnt orange), card-3 `#D97706` (amber).

## Landing page architecture

The landing page (`#landingWrapper`) sits above the app (`#appContainer`) and uses z-ordering with `display: none/block` toggling. It has a full-viewport video background (`bg.mp4`).

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

- **Video background**: `bg.mp4` in `backend/static/`. Served from `/bg.mp4` — FastAPI serves static at `/`, not `/static/`. The landing page video plays only on the landing page; the app pages have a pure white background (no video).
- **Watermark covers**: Two absolutely-positioned `<div>` elements with `::before` (HSL-matched gradient) and `::after` (SVG feTurbulence noise texture) to hide watermarks on the source video. Calibrated via HSL color space: top-left at H245/S10%/L98%→96%, bottom-right at H245/S15%/L90%→88%. Soft edges via box-shadow spread/blur (60px/36px for top-left).
- **Top nav**: Frosted glass effect (`backdrop-filter: blur(10px)`, `rgba(255,255,255,0.32)`). Hamburger menu toggles `.open` class via JS — nav expands from 64px to 230px with CSS `height` transition. Click outside closes the nav. Mobile responsive: cards stack vertically, expanded height 360px.
- **Scenario cards**: Minimalist white cards (`#ffffff`, border-radius 18px). Hover: `translateY(-3px)` + 6-layer amber-to-lavender box-shadow glow. SVG icons in 48px `#eaecf0` circles, hover scale 1.05. Right arrow `›` moves 6px on hover.
- **Blur-in animation**: `@keyframes blurIn` (blur 10px→0, opacity 0→1, translateY -30→0). Title split into `<span class="char">` with 40ms stagger. Subtitle split into `<span class="word">` with 100ms stagger + 300ms initial delay. Pure CSS + vanilla JS.

### Responsive breakpoints

| Breakpoint | Changes |
|------------|---------|
| `max-width: 900px` | Content left 40px, title 56px, scenario-selection max-width 400px |
| `max-width: 600px` | Content relative positioning, title 36px normal wrap, nav margins 20px, cards full-width, overlay full coverage, candidate cards stack vertically |

## App hero area structure

The app hero section (`.hero-input`) is a centered column shown after scenario selection. All app pages use a pure white background — there is no video background on app pages.

```
.hero-input (flex-column, align-items:center, gap:34px, padding: 120px 24px 40px)
  ├── .hero-badge-wrapper (white pill: bg #fff, border-radius 24px)
  │     ├── .hero-badge (dark "★ New" badge, bg #1B1722, z-index:1 floating)
  │     └── .hero-badge-label (scenario name, color #292524)
  ├── .hero-title "UPFLIP" (80px, Fustat 800, color #F5A623)
  ├── .hero-subtitle (20px, Fustat 500, color #78716c)
  └── .search-box (white card: bg #fff, border 1px #e7e5e4, border-radius 22px)
        ├── .sb-top (header row: skill label pill + "Powered by DeepSeek" badge)
        └── .sb-body (white card: bg #fff, border-radius 14px)
              ├── .sb-input-row (textarea + submit button, padding 18px)
              └── .sb-bottom (skill dropdown select + char count, padding 0 18px 16px)
```

**Key behaviors:**
- `.search-box` — clean white card with subtle border and shadow (no longer frosted glass).
- `.sb-top` — muted dark text (`#78716c` / `#a8a29e`). `.sb-skill-label` pill uses `#f5f5f4` background with `#292524` text.
- Skill dropdown (`#heroSkillSelect`) — visible only for Vibe Coding. Populated dynamically from `GET /api/skills`. Options include builtin skills, user-created custom skills, plus two special entries: "自定义规范（仅本次）" (shows inline textarea) and "管理自定义 Skill…" (shows management panel).

## App container

`.app-container` is `max-width: 960px; margin: 0 auto; padding: 40px 24px; background: #ffffff; min-height: 100vh; position: relative; z-index: 1`.

During hero mode (no session active), `.app-container.hero-mode` sets `background: #ffffff; max-width: none; margin: 0; min-height: 100vh; padding: 0`.

## Key files

| File | Role |
|------|------|
| `backend/main.py` | FastAPI app, CORS, static file mount at `/` |
| `backend/routes/optimize.py` | API endpoints: session CRUD + feedback + finalize + skills CRUD |
| `backend/services/claude_client.py` | DeepSeek API wrapper — `generate_candidates()`, `refine_prompt()`, `_build_feedback_text()`, `_parse_targeted_comments()`, `_extract_json()` |
| `backend/services/optimizer.py` | Core protocol: session lifecycle, feedback processing, convergence detection, early finalize |
| `backend/services/skill_loader.py` | File-based skill management — `load_all_skills()`, `get_skill_content()`, `save_custom_skill()`, `delete_custom_skill()`. Reads from `prompts/skills/builtin/` and `prompts/skills/custom/`. |
| `backend/store.py` | In-memory `SessionStore` dict with `SessionState` objects |
| `backend/models/schemas.py` | Pydantic models: `TaskItem`, `CandidateOut`, `SessionOut`, `CreateSessionRequest` (includes `skill_key`), `FeedbackRequest`, `FinalizeResponse` |
| `backend/prompts/system_prompt.py` | Scenario skill models (`VIBECODING_SKILL`, `PPT_SKILL`), round 1 / round N templates. `build_round1_prompt(scenario, custom_rules, skill_key)` resolves quality section: skill_key file → custom_rules inline text → `DEFAULT_QUALITY_SECTION`. `build_roundn_prompt()` returns refinement protocol only (no skill model). |
| `backend/prompts/skills/builtin/*.txt` | 4 builtin quality-standard files: `clean_code.txt`, `react.txt`, `typescript.txt`, `fullstack.txt` |
| `backend/prompts/skills/custom/` | User-created skill files (runtime, persisted to disk). Max 10. |
| `backend/static/index.html` | Complete frontend SPA — scenario selection, candidate cards, task review (vibecoding) or prompt annotation (PPT), @N comment support, skill management UI, final output |

## Two scenarios

The app focuses exclusively on two verticals, selected at startup via card UI:

| Scenario | `scenario` key | Output format | Annotation target |
|----------|---------------|---------------|-------------------|
| Vibe Coding | `vibecoding` | `{blueprint, summary, tasks: [{id, title, prompt}]}` | Per-task sentences |
| PPT制作 | `ppt` | `{prompt}` (flowing prose) | Prompt sentences |

The scenario persists in session state via URL hash. A scenario pill is visible throughout.

## Skill file system

Quality standards are stored as `.txt` files, not hardcoded. Builtin skills ship with the app (`prompts/skills/builtin/`); custom skills are created at runtime (`prompts/skills/custom/`).

**File format**: Plain text. Custom skill files use a `# Display Name` comment on line 1 to store the display name; content starts from line 2.

**Resolution order** in `build_round1_prompt()`:
1. `skill_key` — load content from a named skill file via `get_skill_content()`
2. `custom_rules` — inline ad-hoc text (backward-compatible + "自定义规范（仅本次）")
3. `DEFAULT_QUALITY_SECTION` — built-in fallback (SOLID, DRY, type safety, error handling, observability)

**API**:
- `GET /api/skills` → `{skills: [{id, name, preview, is_custom}, ...]}`
- `POST /api/skills` → create custom skill (body: `{name, content}`), max 10
- `DELETE /api/skills/{skill_id}` → delete custom skill (builtin cannot be deleted)

**Frontend**: The dropdown is populated from `GET /api/skills`. Selecting a skill sends its `id` as `skill_key` in `POST /api/sessions`. "自定义规范（仅本次）" sets `skill_key=null` and sends the textarea content as `custom_rules`. "管理自定义 Skill…" opens an inline CRUD panel.

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/skills` | List all available skills (builtin + custom) |
| `POST` | `/api/skills` | Create a custom skill file |
| `DELETE` | `/api/skills/{skill_id}` | Delete a custom skill (builtin protected) |
| `POST` | `/api/sessions` | Create session — `CreateSessionRequest` includes `idea`, `scenario`, optional `skill_key` and `custom_rules`. DeepSeek generates 1–3 candidates, returns `SessionOut` |
| `GET` | `/api/sessions/{id}` | Restore session state (enables page refresh via URL hash `#<id>`) |
| `POST` | `/api/sessions/{id}/feedback` | Submit `selected_candidate`, `sentences` (with per-sentence votes), optional `comment`. DeepSeek refines. Returns updated `SessionOut` |
| `POST` | `/api/sessions/{id}/finalize` | Return `FinalizeResponse` — read-only, no API call |
| `GET` | `/api/health` | Health check |

## Session lifecycle

1. **Create**: `POST /api/sessions` → `store.create()` → `generate_candidates()` via DeepSeek → return `SessionOut` (phase: `"selection"`, 1–3 candidates)
2. **Feedback** (repeatable): `POST /api/sessions/{id}/feedback` →
   - If round 1 + phase "selection": records chosen angle + content. For vibecoding, stores `blueprint`, `summary`, `tasks`; for PPT, stores `current_prompt`. Switches phase to `"refinement"`.
   - **Early finalize**: If this is the first feedback AND no sentences were annotated AND no comment → skips DeepSeek refinement entirely (returns immediately).
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

**Why Round N excludes the skill model:** The engineering quality standards are baked into the output during Round 1. Re-injecting them in Round N would cause "quality creep" — the LLM adding new requirements each round instead of surgically applying user feedback. The Round N guardrails say "quality must not be stripped away" (defensive) rather than re-teaching the full skill model.

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

**Index convention**: `SentenceFeedback.index` is **0-based** in the backend. All UI rendering (`@N` in comments, sentence badges, feedback labels) uses **1-based** display. `_parse_targeted_comments()` converts `@N` (1-based) → `idx - 1` (0-based internal). `_build_feedback_text()` converts back: `[idx + 1]` (1-based display).

## Vibe Coding output structure

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

## Angle selection design

The system prompt's Protocol Step 2 does NOT give the LLM a fixed list of angle names. Instead, it instructs the LLM to analyze the user's specific idea and derive 1–3 genuinely different approaches from that analysis. If an idea has only one natural architecture, outputting one plan is acceptable — the LLM is told not to pad to 3. This keeps angles specific to each request rather than recycling generic labels.

## Frontend flow

0. **Landing page** — Video background with frosted-glass top nav. Two scenario cards. Blur-in text animation on load. Selecting a scenario hides the landing wrapper and shows the app.
1. **Input** — textarea with scenario-appropriate placeholder. Vibe Coding shows a skill preset dropdown (populated from `/api/skills`); PPT shows nothing in that slot. Character counter at `0/3,000`. Submit button → `POST /api/sessions`.
2. **Selection** — 1–3 candidate cards displayed horizontally in a single row (`#candidatesList` is `display: flex; gap: 20px`). Cards use `flex: 1 1 0; min-width: 260px` — equal-width, side-by-side. No selection header text (kept minimal). Orange left-border accents and orange selected state. At ≤600px, cards stack vertically.
3. **Task review** (vibecoding) — blueprint box at top with summary section below. Task cards in accordion: click header to expand, each task's prompt is split into sentences for left-click=approve / right-click=reject. Per-task ✓保留/✗删除 vote buttons. Sentences are globally numbered across all tasks via `computeGlobalIndices()`.
4. **Annotation** (PPT) — prompt text split into sentences, left-click=approve, right-click=reject, click again=clear.
5. **Actions** — "提交反馈" (primary, orange button), "直接定稿" (orange outlined), "重置所有标注". Comment textarea supports `@N` notation.
6. **Final** — For vibecoding: blueprint + summary + task cards with per-task copy buttons + "复制全部" button. For PPT: prompt text with copy button.

Session ID persists in URL hash (`#<id>`) for refresh recovery. "返回首页" returns to landing.

### Landing → app transition

- `#landingWrapper` and `#appContainer` are mutually exclusive via `.visible` class (toggles `display: none/block`).
- Scenario selection calls `selectScenario(key)` which hides the landing video (`landingBg`), shows the app, and updates the scenario pill.
- URL hash `#<sessionId>` on the app page triggers session restore via `GET /api/sessions/{id}`.

## Frontend edge cases

- Vibe Coding cards gracefully handle a missing `blueprint` field (DeepSeek occasionally omits it) by falling back to show `description` + task count instead of an empty card.
- "直接定稿" button behavior depends on phase: in `"selection"` phase it first calls feedback (to commit the candidate choice, backend skips DeepSeek via early-finalize path) then finalize; in `"refinement"` phase it skips feedback entirely and calls finalize directly.

## Design constraints

- Session state is in-memory only — restarting the server loses all sessions
- DeepSeek API via OpenAI SDK: `deepseek-chat`, max_tokens 6144, timeout 300s
- JSON extraction uses `_extract_json()` with markdown code block + fallback bracket matching (DeepSeek sometimes wraps JSON in ```json```)
- All UI text is Chinese (zh-CN)
- Sentence-splitting normalizes whitespace: `text.replace(/\s+/g, ' ')`. `.` is only treated as a sentence terminator when followed by whitespace or end-of-string (`\.(?=\s|$)`), so filenames like `main.ts` and `schema.prisma` don't get split.
- Per-task sentence annotation uses event delegation on `#taskList` (dynamic content)
- The system python is at `D:/anaconda/python.exe` (Windows `python` alias may resolve to WindowsApps stub)
- Landing page video (`bg.mp4`) is served from `/bg.mp4` (FastAPI static mount at `/`, not `/static/`). App pages have a pure white background — the app video layer has been removed.
- Watermark covers use HSL color space for precise background matching; adjustments should stay in H245 ±5 hue range
- Top nav is positioned at `left:90px; right:40px` (aligned with title text on the left, fluid width)
- Skill files use `_unsafe()` path traversal check — rejects `..`, `/`, `\` in skill IDs
- Custom skills are capped at 10, stored as `.txt` files in `prompts/skills/custom/`
