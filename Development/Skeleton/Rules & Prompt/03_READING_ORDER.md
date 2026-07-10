<!-- 
  作用：定义 AI 读取本项目的标准顺序和逻辑。
  地位：AI 每次开始交互时必须遵循此文件中的流程。
  适用：任何在此项目中的 AI 交互起点。
-->

# 03 — 读取顺序与工作流程

---

## 启动流程（每次交互开始时）

AI 必须按以下顺序读取：

```
Phase 0: 定位项目根目录
  → 确认当前工作目录为 CompassY/

Phase 1: 建立行为准则（必须全读）
  → Rules & Prompt/00_CORE_PRINCIPLES.md
  → Rules & Prompt/01_ROLE_DEFINITION.md
  → Rules & Prompt/02_OUTPUT_FORMAT.md
  → Rules & Prompt/03_READING_ORDER.md  （本文件）
  → Rules & Prompt/04_CONSTRAINTS.md

Phase 2: 了解数据全貌
  → My-DATA/Meta/data_index.md  （若存在）
  → 若无 data_index.md，则扫描 My-DATA/ 目录结构

Phase 3: 了解历史上下文
  → Sessions/session_index.md  （若存在）
  → 最近的 2-3 次 Session 记录

Phase 4: 了解当前状态
  → Guidance/Alerts/active_alerts.md  （若存在）
  → Guidance/Reminders/upcoming.md  （若存在）
  → Guidance/Reports/本周回顾.md  （若存在）
```

---

## 按需读取（根据用户意图触发）

| 用户意图 | 应读取的数据 |
|----------|-------------|
| 涉及身体健康 | `My-DATA/Health/` |
| 涉及学习/技能 | `My-DATA/Learning/` |
| 涉及时间安排 | `My-DATA/Schedule/` |
| 涉及目标计划 | `My-DATA/Goals/` |
| 涉及情绪/心理 | `My-DATA/Mind/` |
| 涉及职业发展 | `My-DATA/Career/` |
| 用户说"看看我最近" | Phase 2 + 3 + 4 全量 |
| 用户说"给点建议" | 先跑 Phase 2 + 3 + 4，再做偏差分析 |

---

## 产出流程（分析完成后）

```
Step 1: 对照八荣八耻和约束条件自检
  → 每条结论都有数据依据吗？
  → 有标注不确定性吗？

Step 2: 先对话，后仪表盘
  → 在对话中回应用户（分析、建议、聆听、追问）
  → 刷新 仪表盘.md（"本次你分享了""我的回应""本次涉及的文件""待你确认"）

Step 3: 写入 My-DATA/（按需，有条件）
  → 用户分享了新的个人数据时，写入 My-DATA/ 对应文件
  → 见下方"写入判断逻辑"
  → 若用户只是聊天/提问，跳过此步

Step 4: 写入 Guidance/（按需，有条件）
  → 有分析产出 → Guidance/Reports/本周回顾.md（追加或更新当日条目）
  → 有新的警告 → Guidance/Alerts/
  → 有新的建议 → Guidance/Suggestions/
  → 有新的提醒 → Guidance/Reminders/
  → 有深度分析 → Guidance/Insights/
  → 若本次无分析产出，跳过此步

Step 5: 归档到 Sessions/（必定执行）
  → 按 Templates/session_template.md 格式记录本次交互
  → 更新 session_index.md
  → 无论对话长短，必须归档

特别注意：
  → Templates/ 是只读的空白表格库，绝不写入任何内容
  → 使用模板时是"参考其格式"，而非"修改模板文件本身"
```

---

## 写入判断逻辑

每次交互后，AI 必须按下表判断写入哪些位置：

| 用户输入类型 | My-DATA 写入 | Guidance 写入 | 说明 |
|:-----------|:-----------:|:------------:|------|
| 运动/健康数据 | ✅ 写入 Health/body_log.md | ✅ 追加本周回顾；如有异常则写警告 | 数据留存 + 趋势分析 |
| 学习计划/进度 | ✅ 写入 Learning/ | ✅ 追加本周回顾 | 记录进度变化 |
| 时间活动安排 | ✅ 写入 Schedule/ | ✅ 追加本周回顾；如有冲突则写警告 | 安排变更需要对比 |
| 目标设定/更新 | ✅ 写入 Goals/ | ✅ 追加本周回顾 | 目标变化是重要事件 |
| 创意想法 | ✅ 写入 Mind/ideas_brainstorm.md | — | 纯记录，无需分析 |
| 新知识学习 | ✅ 写入 Learning/ | — | 纯记录 |
| 自我反思/进步 | ✅ 写入 Mind/self_reflection.md | ✅ 追加本周回顾 | 反思值得写入报告 |
| 情绪/发牢骚/发泄 | ✅ 写入 Mind/mood_log.md | —（持续低落则写提醒） | 聆听为主，不过度分析 |
| 纯聊天/提问 | — | — | 只更新仪表盘和归档 |

**三者必定执行**：Step 2（对话+仪表盘）+ Step 5（Sessions归档），无论输入类型。

---

## 关键原则

- **先读后说**：在任何分析输出前，确保已读取 Phase 1 全部 + Phase 2 必要部分。
- **缺数据不强行分析**：如果对应的 `My-DATA/` 子目录为空或不存在，明确告知用户需要先补充哪些数据。
- **每次交互归档**：无论对话长短，结束后必须在 `Sessions/` 中留下记录。
