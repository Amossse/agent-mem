# Launch drafts — not posted

## English

Agent Mem keeps durable preferences, facts, decisions and procedures in one local store shared by
compatible AI agents. It is a portable Agent Skill with a Python/SQLite CLI, scoped human consent,
layered search/timeline/full retrieval, bounded context, revision conflict checks, expiry and forgetting.

No separate model key, worker or cloud account. The CLI does not scan chat logs or call a network API.
Hosts must actually invoke the Skill; automatic recall and model-driven behavior are not live-verified.
Privacy checks are best-effort. MIT toolkit: https://github.com/Amossse/agent-mem

## 中文

做了 Agent Mem，把值得留的偏好和经验放到同一个本地记忆库，让兼容的 Agent 也能查到。

0.2.0 增加时间线检索和有字符上限的上下文，保留记忆来源与版本，放不下的记录会明确告知。继续支持授权、修改、过期和遗忘，无需额外模型 Key 或后台服务，不扫描聊天历史，不自动上传记忆。

适用于能读取 Skill、执行本地 Python 的宿主，自动调用仍取决于宿主，真实模型行为尚未验证。隐私过滤不能替代人工检查。MIT 开源：https://github.com/Amossse/agent-mem
