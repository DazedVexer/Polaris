# Polaris

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/LLM-OpenAI%20%7C%20DeepSeek%20%7C%20Qwen-green?logo=openai" alt="LLM">
  <img src="https://img.shields.io/badge/DB-SQLite%20%7C%20ChromaDB%20%7C%20FAISS-orange?logo=sqlite" alt="Database">
  <img src="https://img.shields.io/badge/Deploy-FastAPI%20%7C%20React%20%7C%20Docker-2496ED?logo=docker" alt="Deploy">
  <img src="https://img.shields.io/badge/license-MIT-purple" alt="License">
  <img src="https://img.shields.io/badge/status-production%20ready-brightgreen" alt="Status">
</p>


<p align="center">
  <b>一个自托管的 AI Agent：具备长期记忆、RAG、工具调用和自主规划能力。</b>
  <br>
</p>


***

## 项目概述

Polaris 是一个从零构建的 AI Agent 系统，纯 Python + OpenAI SDK，不依赖任何 Agent 框架。整个项目经过六个阶段的渐进式开发（参见 `Development/`），每一步迭代都源于上一阶段的真实痛点——从让 LLM 跑起来，到能记住、能理解、会规划、能动工具、最后打包成 Web 应用。所有 prompt、调度逻辑、工具调用链路都在源码里，无黑盒。

- **六层渐进式架构**——每一层都因为上一层暴露了真实痛点而诞生，不是框架告诉你"该加这一层"
- **零框架依赖**——不依赖 LangChain、LlamaIndex、CrewAI。纯 Python + OpenAI SDK
- **Provider 无关**——Embedding 可换 OpenAI / bge，向量库可换 Chroma / FAISS，LLM 可换 OpenAI / DeepSeek / Qwen
- **CLI + Web 双模式**——双击 `.bat` 启动 CLI，`docker-compose up` 启动 Web UI
- **开箱即用**——天气查询、GitHub Issue、文件系统操作、插件式工具注册：加一个新工具只需 3 行代码

```
"你" → /agent "查一下北京今天天气。如果下雨，帮我在 GitHub 建 Issue 提醒我带伞。"

Polaris:
  Step 1 — get_weather("Beijing")     → "28°C，中雨"
  Step 2 — 分析结果                    → "今天会下雨"
  Step 3 — create_issue(...)          → "Issue #42 已创建 ✓"
  完成。
```

***

## 架构

项目经过 6 个阶段的渐进式开发，`Development/` 目录中保留了每次迭代的完整快照。

**Phase 1 — 核心引擎**：规则驱动的 system prompt + OpenAI 流式对话 + 会话归档，LLM 带着人格跑起来。

**Phase 2 — 记忆层**：加入短期记忆（滑动窗口）和长期记忆（SQLite 持久化），LLM 自动从对话中提取关键信息存入记忆库。

**Phase 3 — RAG 检索**：引入 embedding（OpenAI / bge）和向量数据库（Chroma / FAISS），知识库支持 md/pdf 文档的语义检索，跨越关键词匹配的局限。

**Phase 4 — Agent 循环**：Planner 拆解任务 → Executor 逐步执行 → Reflection 质检，形成 Plan-Execute-Reflect 闭环，Agent 具备多步推理和失败自愈能力。

**Phase 5 — 工具系统**：插件式工具注册 + OpenAI Function Calling，内置天气、GitHub、文件系统工具，新增工具只需 3 行代码注册。

**Phase 6 — 产品化**：FastAPI 后端 + React 前端 + Docker Compose 一键部署，从 CLI 走向 Web 应用。

***

## 快速开始

### 前置条件

- Python 3.10+
- OpenAI 兼容的 API Key（[OpenAI](https://platform.openai.com)、[DeepSeek](https://platform.deepseek.com)、[Qwen](https://dashscope.console.aliyun.com) 等）
- 安装 Node.js（仅 Web 前端开发时需要）

### CLI 模式

```bash
git clone https://github.com/yourusername/Polaris.git
cd Polaris

pip install -r requirements.txt
cp .env.example .env
# 编辑 .env → 填入 OPENAI_API_KEY

python main.py
# 或者双击 启动CLI模式.bat
```

### Web 模式

```bash
docker-compose up -d
# 打开 → http://localhost:8000
# API 文档 → http://localhost:8000/docs
```

***

## 项目结构

```
Polaris/
│
├── main.py                      # CLI 入口
├── config.py                    # 所有配置集中管理
│
├── core/                        # Agent 核心循环
│   ├── agent_loop.py            # Plan → Execute → Reflect 编排器
│   ├── task_planner.py          # 用户指令 → 结构化步骤计划
│   ├── executor.py              # 逐步执行 + Function Calling 工具调用
│   └── reflection.py            # 质检 → 步骤重试 / 方案重规划 / 完成
│
├── memory/                      # 记忆系统
│   ├── short_term_memory.py     # 滑动窗口 STM + 自动摘要触发
│   ├── long_term_memory.py      # SQLite 持久化 + embedding + 情绪/画像表
│   └── memory_manager.py        # LLM 驱动记忆提取 / 检索 / 总结
│
├── retrieval/                   # 检索 + 知识库
│   ├── retrieval_pipeline.py    # 双路召回（记忆 + 知识库）→ 统一排序
│   ├── knowledge_base.py        # md/pdf 加载 + 分块 + 向量化入库
│   └── vector_store.py          # 统一向量数据库（Chroma | FAISS）
│
├── llm/                         # LLM 接口层
│   ├── llm_client.py            # OpenAI 兼容流式客户端（重试 + 指数退避）
│   ├── embedding.py             # 统一 embedding（OpenAI | bge 本地）
│   └── prompt_builder.py        # rules/*.md → system prompt + BangBand 动态注入
│
├── perception/                  # 情绪与意图感知（BangBand）
│   └── perception.py            # 每轮对话静默分析 mood / intent / intensity
│
├── session/                     # 会话归档
│   └── session_manger.py        # JSON 对话存档：创建 / 追加 / 加载
│
├── tools/                       # 工具系统
│   ├── tool_registry.py         # 插件式注册中心 + OpenAI Function Calling
│   ├── weather.py               # OpenWeatherMap 天气查询
│   ├── github.py                # Issue 创建 / 仓库查询 / 用户仓库列表
│   ├── filesystem.py            # 安全沙箱：读 / 写 / 列目录 / 搜索
│   └── __init__.py              # 批量注册入口
│
├── server/                      # FastAPI 后端
│   ├── main.py                  # 应用入口 + /health 健康检查
│   ├── models.py                # Pydantic 请求/响应模型
│   ├── middleware.py             # CORS + 请求日志 + API Token 认证
│   └── api/
│       ├── chat.py              # /api/chat · stream · agent · agent/stream
│       ├── memory.py            # /api/memory 列表 / 搜索 / 删除
│       ├── knowledge.py         # /api/knowledge 状态 / 搜索 / 上传 / 重建
│       └── tools.py             # /api/tools 工具列表
│
├── web/                         # React + TypeScript 前端
│   ├── src/
│   │   ├── components/          # ChatWindow · AgentPanel · MemoryPanel · KnowledgePanel · Sidebar · ToolStatus · MessageBubble
│   │   ├── api.ts               # 后端 API 客户端封装
│   │   ├── types.ts             # TypeScript 类型定义
│   │   ├── App.tsx              # 根组件（路由 + 布局）
│   │   └── App.css              # 全局样式
│   ├── index.html               # Vite 入口 HTML
│   ├── package.json             # 前端依赖
│   ├── tsconfig.json            # TypeScript 配置
│   └── vite.config.ts           # Vite 构建配置
│
├── rules/                       # Agent 人格规则（6 个 .md）
├── sessions/                    # 对话存档目录
├── kb/                          # 知识库文档目录
│
├── Dockerfile                   # 多阶段构建
├── docker-compose.yml           # 一键部署
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
├── 启动CLI模式.bat               # Windows 双击启动 CLI
└── 启动Web模式.bat               # Windows 双击启动 Web
```

***

## 配置

```bash
cp .env.example .env
```

**必填**

| 变量              | 说明                                            |
| ----------------- | ----------------------------------------------- |
| `OPENAI_API_KEY`  | API Key（OpenAI / DeepSeek / Qwen）             |
| `OPENAI_BASE_URL` | API 端点（默认 `https://api.openai.com/v1`）    |
| `OPENAI_MODEL`    | 模型（`gpt-4o` / `deepseek-chat` / `qwen-max`） |

**Embedding（可选）**

| 变量                 | 默认值   | 可选              |
| -------------------- | -------- | ----------------- |
| `EMBEDDING_PROVIDER` | `openai` | `bge`（免费本地） |

**向量库（可选）**

| 变量                 | 默认值   | 可选    |
| -------------------- | -------- | ------- |
| `VECTOR_DB_PROVIDER` | `chroma` | `faiss` |

**工具（可选）**

| 变量                  | 用途                          |
| --------------------- | ----------------------------- |
| `OPENWEATHER_API_KEY` | 天气查询                      |
| `GITHUB_TOKEN`        | GitHub 操作（需 `repo` 权限） |

***

## API 参考

启动后访问 `http://localhost:8000/docs` 查看完整交互式文档。

| 方法     | 路径                     | 说明                  |
| -------- | ------------------------ | --------------------- |
| `POST`   | `/api/chat`              | 非流式对话            |
| `POST`   | `/api/chat/stream`       | SSE 流式              |
| `POST`   | `/api/chat/agent`        | Agent 任务执行        |
| `POST`   | `/api/chat/agent/stream` | Agent + 每步 SSE 进度 |
| `GET`    | `/api/memory`            | 记忆列表              |
| `POST`   | `/api/memory/search`     | 语义搜索记忆          |
| `DELETE` | `/api/memory/{id}`       | 删除记忆              |
| `GET`    | `/api/knowledge/status`  | 知识库状态            |
| `POST`   | `/api/knowledge/search`  | 语义搜索知识库        |
| `POST`   | `/api/knowledge/upload`  | 上传文档              |
| `POST`   | `/api/knowledge/rebuild` | 重建知识库            |
| `GET`    | `/api/tools`             | 可用工具列表          |
| `GET`    | `/health`                | 健康检查              |

|      |      |      |
| ---- | ---- | ---- |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
|      |      |      |
