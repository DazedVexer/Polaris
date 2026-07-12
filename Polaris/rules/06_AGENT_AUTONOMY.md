# 06 — Agent Autonomy Specification

## Autonomy Levels

| Level | Name | Can Do | Cannot Do | Trigger |
|-------|------|--------|-----------|---------|
| **L0** | Read-only | Query data, generate reports, analyze trends | Create/modify any files | Auto-triggered, no confirmation needed |
| **L1** | Suggest | L0 + proactively suggest action plans to user | Auto-execute without confirmation | Anomaly detected or user implies need |
| **L2** | Execute | L1 + execute low-risk operations | Modify schedule, send messages on behalf of user | After user confirmation |
| **L3** | Full | Any operation | — | Manual `/agent` command only |

## Autonomous Trigger Rules

1. Files NEVER autonomously modified: `data/schedule/`, `data/goals/`, any file marked "important" by user
2. Can autonomously READ: all `data/` directories, `mood_log`, `memories`
3. Can autonomously CREATE: `sessions/`, temporary analysis reports in `data/analysis/`
4. MUST ask for confirmation: modifying existing files, sending emails/messages, changing schedules

## Decision Engine Guidelines

- Not every round calls LLM — rule-based pre-check first
- High intensity negative emotion (anxious/sad/frustrated/angry) → directly suggest agent mode
- Multiple anomalies detected → suggest agent mode
- Grey areas (consulting/planning intent) → consult LLM for decision
- `auto_agent` strictly limited to L0 read-only tasks
- `alert` triggers: data anomaly AND user hasn't checked in recently
