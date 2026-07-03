# CompassY
Personal AI Executive Assistant
---

## What is CompassY?

CompassY 是一个 **Personal AI Executive Assistant（个人 AI 执行助理）** 项目的产品设计雏形（Project Skeleton）——通过一套严密的规则体系与模板库，将 AI 转化为基于真实个人数据的、冷静务实的"人生副驾驶"（Life Co-Pilot）。

---

## Why?

在信息爆炸的时代，个人数据分散在聊天记录、备忘录、健康 App、日历、笔记等各处，却没有人帮你**串联分析、发现偏差、预警风险、追踪进度**。

CompassY 解决的核心问题：

- **数据孤岛**：你的健康数据、学习进度、日程安排、目标计划互不关联，缺乏交叉分析
- **缺乏外部视角**：自己很难对自己的行为模式做客观偏差检测
- **遗忘与脱轨**：设定目标后缺乏持续追踪和提醒机制，容易偏离
- **交互无记忆**：每次和 AI 聊天都是独立的，没有累积的个人上下文
- **AI 角色模糊**：普通 AI 助手要么过于讨好、要么缺乏边界，CompassY 通过严格的角色定义让 AI 成为稳定可靠的分析型伙伴


---

## Features

### 核心能力

| 能力             | 说明                                                         |
| ---------------- | ------------------------------------------------------------ |
| **数据整合分析** | 跨领域关联你的健康、学习、日程、目标、情绪数据，发现隐藏模式 |
| **偏差检测**     | 对照目标与实际行为，自动发现偏离并给出可执行方案             |
| **风险预警**     | 基于数据趋势，提前发出分级警告（红/黄/绿），附带应对方案     |
| **进度追踪**     | 持续追踪目标达成进度，阶段性总结回顾                         |
| **盲区发现**     | 分析你忽略或没有数据的领域，主动提醒补充                     |
| **完整归档**     | 每次交互必定归档，形成可检索的长期个人历史                   |
| **周期性报告**   | 日条目 → 周回顾 → 月汇总，三级报告体系自动运转               |

### 设计原则

- **数据驱动**：所有输出必须有 My-DATA 中的真实数据依据，严禁猜测
- **标准化输出**：建议、警告、纠错、提醒——四种格式统一、结构清晰
- **渐进式修改**：重大建议分阶段提出，每阶段可独立验证
- **敏感数据保护**：姓名、密码、位置、医疗、财务五类敏感信息分级保护
- **角色边界清晰**：不做医学诊断、不替代心理治疗、不替用户做决定、不预测未来

### 当前架构

```
Rules & Prompt/    → 5 个规则文件，定义 AI 的行为准则、角色、输出格式、工作流程、约束
Templates/         → 7 个模板文件，标准化数据条目、目标、周报、月报、警告、提醒、会话归档
My-DATA/           → 用户个人数据（待填充）
Guidance/          → AI 分析产出：报告、警告、建议、提醒、深度洞察
Sessions/          → 每次交互的完整归档
仪表盘.md          → 每次交互的摘要面板
```

---

## Future

CompassY 目前是在 AI IDE 中以纯 Markdown 规则文件构建的构思雏形，即 Project Skeleton，后续将逐步演进为一个真正的 **AI Agent 项目**。

### 往后计划

#### Phase 1 可运行系统（Runnable Agent）
* CLI聊天入口（`main.py`）
* session自动保存（JSON）
* prompt自动拼接
* 基础上下文记忆（短期）

#### Phase 2 记忆系统（Memory Layer）
* long-term memory（JSON/SQLite）
* memory写入策略（LLM判断是否存储）
* memory读取策略（相关性匹配）
* 自动总结（conversation summarization）

#### Phase 3 知识系统（RAG）
* embedding（OpenAI / bge）
* vector database（Chroma / FAISS）
* knowledge base（md/pdf）
* retrieval pipeline

#### Phase 4 Agent化（Planner + Executor）
* Task Planner（任务拆解）
* Executor（逐步执行）
* Reflection（自我修正）
* 多轮任务链

#### Phase 5 工具系统（Tool Use / Function Calling）
* tool registry
* function calling
* API接入（天气 / GitHub / 文件系统）
* tool routing

#### Phase 6：产品化（Web + Deployment）
* FastAPI后端
* Web UI（React / Next）
* 用户界面
* Docker部署
* API管理