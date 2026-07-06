* # Polaris

## Personal AI Executive Assistant

## What is CompassY?

Polaris 是一个**个人 AI 执行助理**，将 LLM 转化为有纪律的、数据驱动的生活教练。它不只是一个泛泛的聊天机器人——Polaris 在一套严密的规则体系下运行，定义其角色、输出格式、约束和分析人格。它能帮你：

- **串联**分散在健康、学习、日程、目标中的个人数据
- **发现**行为与目标的偏离
- **预警**风险（分级警告：红 / 黄 / 绿）
- **记住**一切——每次交互自动归档、可检索
- **报告**进度（每日条目 → 每周回顾 → 每月汇总）

Polaris 不是医生、不是心理治疗师、也不是算命先生。它是一个**分析型伙伴**，有明确的边界，始终基于*你的*真实数据工作。Why?

***

## 架构

### Phase 1 — 可运行 CLI Agent ✅

一个功能完整的 CLI Agent，具备角色感知的 system prompt、流式对话、滑动窗口短期记忆和自动会话归档。

| 模块                 | 职责                                        |
| -------------------- | ------------------------------------------- |
| `prompt_builder.py`  | 加载 `rules/*.md`，拼接为复合 system prompt |
| `llm_client.py`      | OpenAI 兼容的流式聊天，含重试逻辑           |
| `memory.py`          | 滑动窗口短期上下文（STM）                   |
| `session_manager.py` | 每次对话自动保存为 JSON                     |
| `main.py`            | 调度器 — `/exit`、`/save`、优雅异常处理     |

### Phase 2 — 记忆层 🚧（进行中）

增加持久化长期记忆，由 LLM 驱动记忆提取、检索和总结。

| 模块                   | 职责                         |
| ---------------------- | ---------------------------- |
| `short_term_memory.py` | 增强版 STM，含总结触发机制   |
| `long_term_memory.py`  | 基于 SQLite 的持久化记忆存储 |
| `memory_manager.py`    | 记忆提取、检索与总结调度器   |
| `config.py`            | 双阶段扩展配置               |
	
***

## 当前架构（Phase 2）

```
Polaris/
├── main.py                     # CLI 入口，对话循环 + 记忆层集成
├── config.py                   # .env 配置加载 + 双阶段参数
├── prompt_builder.py           # 加载 rules/*.md → system prompt
├── llm_client.py               # OpenAI 兼容流式聊天 + 重试
├── short_term_memory.py        # 短期记忆 (STM)，支持总结触发
├── long_term_memory.py         # SQLite 持久化长期记忆库 (LTM)
├── memory_manager.py           # 记忆管家：提取 / 检索 / 总结调度
├── session_manger.py           # 对话自动归档为 JSON
├── rules/                      # 5 个规则文件，定义 LLM 角色行为
└── sessions/                   # 对话存档目录
```

***

## 快速开始

### 前置条件

- Python 3.10+
- 一个 OpenAI 兼容的 API 端点（OpenAI、DeepSeek、Qwen 等）

### 安装配置

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/CompassY.git
cd CompassY

# 2. 安装依赖
pip install openai python-dotenv

# 3. 配置 API 密钥
# 进入 Phase 1 或 Phase 2 目录：
cd "Phase 1：Runnable System"
echo OPENAI_API_KEY=sk-your-key-here     > .env
echo OPENAI_BASE_URL=https://api.openai.com/v1 >> .env
echo OPENAI_MODEL=gpt-4o                 >> .env

# 4. 启动 Polaris
python main.py
```

### 使用示例

```
Polaris/
├── main.py                     # CLI 入口，对话循环 + 记忆层集成
├── config.py                   # .env 配置加载 + 双阶段参数
├── prompt_builder.py           # 加载 rules/*.md → system prompt
├── llm_client.py               # OpenAI 兼容流式聊天 + 重试
├── short_term_memory.py        # 短期记忆 (STM)，支持总结触发
├── long_term_memory.py         # SQLite 持久化长期记忆库 (LTM)
├── memory_manager.py           # 记忆管家：提取 / 检索 / 总结调度
├── session_manger.py           # 对话自动归档为 JSON
├── rules/                      # 5 个规则文件，定义 LLM 角色行为
└── sessions/                   # 对话存档目录
```

***

## 配置说明

所有配置存放在项目根目录的 `.env` 文件中。启动时 Polaris 会校验配置，缺失项会给出明确的中文错误提示。

| 变量              | 必填 | 说明                                     |
| :---------------- | :--- | :--------------------------------------- |
| `OPENAI_API_KEY`  | 是   | API 密钥                                 |
| `OPENAI_BASE_URL` | 是   | API 端点地址                             |
| `OPENAI_MODEL`    | 是   | 模型名称（如 `gpt-4o`、`deepseek-chat`） |

Phase 2 中 `config.py` 额外可调参数：

| 参数                    | 默认值 | 说明                               |
| :---------------------- | :----- | :--------------------------------- |
| `STM_WindowSize`        | 10     | 短期记忆保留的最大对话轮数         |
| `STM_SUMMARY_TRIGGER`   | 18     | 消息数达到此阈值时触发自动总结     |
| `LTM_RETRIEVAL_K`       | 5      | 每次对话从长期记忆中检索的最大条数 |
| `LLM_MEMORY_EXTRACTION` | 5      | 每隔 N 轮对话触发一次记忆提取      |

***

## 设计原则

1. **自包含** — 规则是纯 Markdown 文件，不硬编码任何 prompt。LLM 从 `rules/` 中读取自己的角色定义，行为透明、可审计。
2. **数据驱动** — 所有输出必须以用户的真实数据为依据。规则体系禁止猜测。
3. **边界清晰** — Polaris 明确不做医学诊断、不替代心理治疗、不算命、不替用户做决定。
4. **渐进式交付** — 重大建议分阶段提出，每个阶段可独立验证。
5. **敏感数据保护** — 姓名、密码、位置、医疗、财务五类敏感信息分级保护。

***

## 路线图

| 阶段        | 状态     | 重点                                            |
| :---------- | :------- | :---------------------------------------------- |
| **Phase 1** | ✅ 已完成 | 可运行 CLI Agent，规则驱动的 system prompt      |
| **Phase 2** | 🚧 进行中 | 长期记忆：SQLite 持久化、LLM 记忆提取与检索     |
| **Phase 3** | 规划中   | RAG 知识系统（embedding、向量数据库、检索管线） |
| **Phase 4** | 规划中   | Agent 能力：任务规划、逐步执行、自我反思        |
| **Phase 5** | 规划中   | 工具调用（天气、GitHub、文件系统、API）         |
| **Phase 6** | 规划中   | 产品化：FastAPI 后端、React 界面、Docker 部署   |

