* # CompassY

	## Personal AI Executive Assistant

	## What is CompassY?

	CompassY 是一个 **Personal AI Executive Assistant（个人 AI 执行助理）** 项目——通过一套严密的规则体系与模板库，将 AI 转化为基于真实个人数据的、冷静务实的"人生副驾驶"（Life Co-Pilot）。当前已完成 Phase 1 可运行 CLI Agent，正在向完整 AI Agent 演进。

	***

	## Why?

	在信息爆炸的时代，个人数据分散在聊天记录、备忘录、健康 App、日历、笔记等各处，却没有人帮你**串联分析、发现偏差、预警风险、追踪进度**。

	CompassY 解决的核心问题：

	- **数据孤岛**：你的健康数据、学习进度、日程安排、目标计划互不关联，缺乏交叉分析
	- **缺乏外部视角**：自己很难对自己的行为模式做客观偏差检测
	- **遗忘与脱轨**：设定目标后缺乏持续追踪和提醒机制，容易偏离
	- **交互无记忆**：每次和 AI 聊天都是独立的，没有累积的个人上下文
	- **AI 角色模糊**：普通 AI 助手要么过于讨好、要么缺乏边界，CompassY 通过严格的角色定义让 AI 成为稳定可靠的分析型伙伴

	***

	## Features

	### 核心能力

	| 能力         | 说明                             |
	| ---------- | ------------------------------ |
	| **数据整合分析** | 跨领域关联你的健康、学习、日程、目标、情绪数据，发现隐藏模式 |
	| **偏差检测**   | 对照目标与实际行为，自动发现偏离并给出可执行方案       |
	| **风险预警**   | 基于数据趋势，提前发出分级警告（红/黄/绿），附带应对方案  |
	| **进度追踪**   | 持续追踪目标达成进度，阶段性总结回顾             |
	| **盲区发现**   | 分析你忽略或没有数据的领域，主动提醒补充           |
	| **完整归档**   | 每次交互必定归档，形成可检索的长期个人历史          |
	| **周期性报告**  | 日条目 → 周回顾 → 月汇总，三级报告体系自动运转     |

	### 设计原则

	- **数据驱动**：所有输出必须有 My-DATA 中的真实数据依据，严禁猜测
	- **标准化输出**：建议、警告、纠错、提醒——四种格式统一、结构清晰
	- **渐进式修改**：重大建议分阶段提出，每阶段可独立验证
	- **敏感数据保护**：姓名、密码、位置、医疗、财务五类敏感信息分级保护
	- **角色边界清晰**：不做医学诊断、不替代心理治疗、不替用户做决定、不预测未来

	### 当前架构（Phase 1：Runnable System）

	```
	Phase 1：Runnable System/
	├── main.py                   # CLI 聊天入口
	├── config.py                 # 配置加载（.env + 路径）
	├── prompt_builder.py         # 读取 rules/ 拼接 system prompt
	├── llm_client.py             # LLM API 调用封装
	├── session_manager.py        # 会话自动保存（JSON）
	├── memory.py                 # 短期上下文记忆（滑动窗口）
	├── rules/                    # 规则文件（自包含，不外求）
	│   ├── 00_CORE_PRINCIPLES.md
	│   ├── 01_ROLE_DEFINITION.md
	│   ├── 02_OUTPUT_FORMAT.md
	│   ├── 03_READING_ORDER.md
	│   └── 04_CONSTRAINTS.md
	└── sessions/                 # 对话存档
	```

	***

	## Future

	Phase 1 可运行 CLI Agent 已交付，这是 CompassY 的第一个里程碑：打开终端输入 `python main.py`，就能和一个有明确角色人格的 AI 对话。背后是 5 个模块协同工作——`prompt_builder.py` 加载 `rules/` 下 5 个规则文件拼成 system prompt，将「冷静分析型伙伴」的角色定义注入 LLM；`llm_client.py` 封装 API 调用，兼容 GPT / DeepSeek / Qwen 等任意模型，密钥写在 `.env`；`memory.py` 用滑动窗口维护短期上下文，确保 LLM 在同一个 session 内不会失忆；`session_manager.py` 把每次对话自动存为 JSON 归档；`main.py` 统筹以上所有模块，提供 `/exit` 退出、`/save` 存档，异常不崩溃。这轮 Phase 验证了核心设计的可行性：Markdown 规则确实能驱动 LLM 按设定角色行事，自包含架构真正做到了搬家即用，从用户输入到回复归档的数据闭环全自动跑通。

	### 往后计划

	#### Phase 2 记忆系统（Memory Layer）

	- long-term memory（JSON/SQLite）
	- memory 写入策略（LLM 判断是否存储）
	- memory 读取策略（相关性匹配）
	- 自动总结（conversation summarization）

	#### Phase 3 知识系统（RAG）

	- embedding（OpenAI / bge）
	- vector database（Chroma / FAISS）
	- knowledge base（md/pdf）
	- retrieval pipeline

	#### Phase 4 Agent 化（Planner + Executor）

	- Task Planner（任务拆解）
	- Executor（逐步执行）
	- Reflection（自我修正）
	- 多轮任务链

	#### Phase 5 工具系统（Tool Use / Function Calling）

	- tool registry
	- function calling
	- API 接入（天气 / GitHub / 文件系统）
	- tool routing

	#### Phase 6：产品化（Web + Deployment）

	- FastAPI 后端
	- Web UI（React / Next）
	- 用户界面
	- Docker 部署
	- API 管理
