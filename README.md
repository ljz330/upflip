# UPFLIP — User Preference Feedback Loop Improver for Prompts

一个基于**句子级用户偏好反馈**的提示词迭代精炼工具。输入一个模糊想法，AI 从多个角度生成候选方案，你来逐句标注「认可」或「反对」，系统像对话一样逐步打磨，直到你满意——全程你只需要点鼠标。

```
模糊想法 → 多角度方案生成 → 选择方向 → 逐句标注 → AI 精炼 → 收敛定稿
```

## 🧭 为什么需要 UPFLIP

### 问题出在哪里

VibeCoding 中，开发者通常能说清「要做什么」和「怎么做」，但**「按什么规范做」**——技术细节、架构约束、代码风格——往往只存在于脑海里，没有写进提示词。LLM 收不到这些信号，就只能自行猜测，产出的代码自然偏离你的预期。

这不是模型能力的问题。同一个 DeepSeek，有人写出的提示词产出大厂级代码，有人拿到的却是跑不起来的 demo——**差距完全在提示词质量**。

### 谁在用

- **VibeCoding 新手**：有想法但不知道怎么组织成工程级提示词
- **独立创作者 / 自由开发者**：没有团队的代码规范沉淀，需要一套开箱即用的标准

### 怎么解决

UPFLIP 的做法不是给你一个「万能提示词模板」，而是模拟**优秀程序员的思路**：拿到模糊需求后，主动补全缺失的规范层——技术栈取舍、目录结构、数据模型、任务拆分——把一句话扩充为一套**符合工程标准的项目蓝图**。同时通过逐句反馈让你掌控方向，不让 LLM 替你瞎猜。

## 🎯 核心理念：像对话一样打磨提示词

传统做法是你一个人对着输入框反复改 prompt，效果完全依赖你的 prompt engineering 经验。UPFLIP 把这件事变成了**结构化的人机协作**：

| 传统方式 | UPFLIP |
|---------|--------|
| 自己猜怎么改，改完不知道对不对 | AI 从 3 个角度出方案，你只需选择 |
| 逐字逐句手动重写 | 左键认可 / 右键反对，逐句反馈 |
| 每次都需要你组织语言提要求 | `@N` 写法精准指向某一句话，浅白自然 |
| 靠感觉判断是否"差不多了" | 算法自动检测收敛，建议何时定稿 |

它的核心不是什么神奇的 prompt 模板，而是**一个机器能理解、人能轻松配合的反馈协议**——你把偏好表达给机器，机器把工程能力注入回 prompt。

## 🔁 迭代流程

### Round 1：发散生成
输入模糊想法 → DeepSeek 分析意图 → 生成 1–3 个**架构本质上不同**的方案（不是换个说法的同一方案）

### 逐句标注
选择方案后，提示词被自动拆分为句子：
- **左键点击** → 绿色认可（这句话保留）
- **右键点击** → 红色反对（这句话改掉）
- **再次点击** → 清除标记
- `@N 换用 REST 接口` → 精准告诉 AI 把第 N 句话怎么改

### Round N：收敛精炼
提交反馈 → DeepSeek 只改动你反对的部分，你认可的内容**原封不动保留**。每次精炼后重新标注，直到满意。

### 智能收敛
当 Round ≥ 3、反对句子 ≤ 1、没有额外意见时，系统自动提示「可以定稿了」。

## 🧩 可更换的 Skill 模型

UPFLIP 不把工程标准写死在代码里。Skill 模型是一个**可插拔的规则层**，定义了「什么是好的 prompt / blueprint / tasks」：

```
VIBECODING_SKILL          ← SOLID / DRY / 类型安全 / 错误处理 / 可观测性
PPT_SKILL                 ← 受众分析 / 叙事架构 / 幻灯片组成 / 数据故事化 / 视觉语言

DEFAULT_QUALITY_SECTION   ← 默认代码质量规范（可被用户替换）
```

**Vibe Coding 场景**在搜索框提供下拉预设：默认 Clean Code 规范、React 最佳实践、TypeScript 严格模式、全栈项目规范，或填入你自己的规范——你的规范会**整体替换**默认质量标准，而不是简单拼接。

**Round 1 注入 Skill，Round N 不注入**——这是一个刻意的设计选择。工程标准在 Round 1 已经融入输出了，后续精炼只做「防守」而非「加码」。如果每轮都重新注入 Skill 模型，LLM 会忍不住在每次精炼中额外添加新需求，导致**质量膨胀**——输出越来越长，偏离用户实际反馈。

## 💰 降成本设计（Token 节省）

| 机制 | 方式 | 节省量 |
|------|------|--------|
| **反馈格式压缩** | 认可/未标记的句子只传序号 `[1] [2] [4]`，不传原文 | ~52% 反馈 token |
| **反对句保留全文** | 只有要改的句子才传原文，给 LLM 替换上下文 | — |
| **Round N 去除 Skill** | 系统提示从 ~5000 chars 降至 ~2200 chars | ~2800 chars/轮 |
| **@N 针对性意见** | 一行 `@3 改用 REST` 替代一段「第三句话改成...」的描述 | 显著减少用户输入 token |
| **单文件 SPA** | 前端零依赖、零构建，一个 HTML 解决全部 | 无 |

### 反馈格式对比

传统方式（每句话都传全文）：
```
认可的句子：项目采用 React + TypeScript 技术栈，使用 Vite 作为构建工具…
反对的句子：数据层使用 GraphQL 统一查询接口。
未标注的句子：状态管理使用 Zustand 轻量方案。
→ 约 800 tokens
```

UPFLIP 方式（认可的只传编号）：
```
认可的句子（保留原文）：[1] [2] [4]
反对的句子：
- [3] 数据层使用 GraphQL 统一查询接口。
  用户针对此句的意见：改用 REST
→ 约 120 tokens，节省 ~85%
```

## 📁 两个垂直场景

| 场景 | 输出 | 特点 |
|------|------|------|
| **Vibe Coding** | 项目蓝图 + 摘要 + 3–5 个独立可执行任务 prompt | 每张任务卡片内部逐句标注，任务间有依赖顺序 |
| **PPT 制作** | 一段 8–15 句的流畅提示词 | 整体逐句标注，从受众分析到数据故事化 |

## 🛠 技术栈

```
浏览器 (index.html)  ←→  FastAPI (Python)  ←→  DeepSeek API (deepseek-chat)
  单文件 SPA                内存会话                 OpenAI SDK 兼容协议
```

- **后端**：Python + FastAPI，零数据库（内存 `SessionStore`，UUID 键值）
- **前端**：单个 HTML 文件，Vanilla JS + CSS，无框架无构建
- **LLM**：DeepSeek (`deepseek-chat`)，通过 OpenAI SDK 调用
- **无持久化**：重启服务即丢失所有会话

## 🚀 本地运行

```bash
# 1. 设置 API Key
# 在 .env 中写入：DEEPSEEK_API_KEY=sk-...

# 2. 安装依赖
pip install -r backend/requirements.txt

# 3. 启动（Windows PowerShell）
$env:PYTHONPATH="backend"
python -m uvicorn backend.main:app --reload --port 8080

# 4. 浏览器打开
# http://localhost:8080
```

## 📡 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/sessions` | 创建会话，DeepSeek 生成候选方案 |
| `GET` | `/api/sessions/{id}` | 恢复会话（刷新页面用） |
| `POST` | `/api/sessions/{id}/feedback` | 提交逐句反馈，DeepSeek 精炼 |
| `POST` | `/api/sessions/{id}/finalize` | 定稿（只读，不调 API） |

## 📂 项目结构

```
backend/
├── main.py              # FastAPI 入口，静态文件挂载
├── store.py             # 内存会话存储
├── routes/optimize.py   # API 路由
├── services/
│   ├── claude_client.py # DeepSeek 封装 + 反馈格式构建
│   └── optimizer.py     # 会话生命周期、收敛检测
├── models/schemas.py    # Pydantic 数据模型
├── prompts/
│   └── system_prompt.py # Skill 模型 + Round 1/N 模板
└── static/
    └── index.html       # 完整前端 SPA
```

## ⚠️ 设计约束

- 会话存储在内存中，重启服务所有数据丢失
- DeepSeek 输出有时会包裹在 ` ```json ``` ` 中，后端通过 `_extract_json()` 兼容处理
- 前端句子拆分对文件名做了特殊处理：`main.ts`、`schema.prisma` 不会被错误切分
- 所有 UI 文本为中文，技术术语保留英文
- `backdrop-filter: blur()` 会创建层叠上下文裁剪子元素，搜索框设为 `overflow: visible` 以确保下拉菜单正常显示
