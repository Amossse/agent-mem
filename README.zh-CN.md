# Agent Mem

把值得保留的经验记一次，让另一个 Agent 也能查到。

一个通用 Agent Skill，加一个本地记忆管理 CLI。兼容的 Agent 共用 SQLite 文件和命名空间，保存偏好、事实、决策与操作经验。[English](README.md)

## 安装与使用

记忆输入会拒绝重复的 JSON 字段，不会静默采用最后一个值；拒绝的记录不会写入数据库。

需要 Python 3.10+。运行时没有第三方依赖，不需要 API Key、后台服务或额外模型。通过 GitHub 安装，未发布到 PyPI：

```sh
uv tool install --python 3.11 git+https://github.com/Amossse/agent-mem.git@main
cd your-project
agent-mem install --agent all
```

也可用 `pipx install git+https://github.com/Amossse/agent-mem.git@main`。`main` 包含 0.2.0 升级，既有 `v0.1.0` 标签保持不变。
安装后，新开 Codex 或 Claude Code 会话，调用 `$agent-mem` 或 `/agent-mem`，例如：

> 记住我的学习卡片每张只放一个问题，附一个简短例子。使用当前项目的本地记忆库，命名空间为 study；开启持续写入前先问我。

确认授权后，Agent 应保存简短记忆并返回 ID。换一个兼容 Agent，指定同一个数据库和命名空间即可查询。安装 Skill 不保证自动调用，也不会自动修改宿主的启动规则。

升级时，先升级 Python 包，再把旧项目里的 Skill 文件夹移到安装目录之外备份，重新执行安装。自定义修改应核对后再恢复。安装器仍会拒绝不同的既有文件，避免覆盖手工修改。已有 schema-v1 记忆库无需迁移，不要移动或删除数据库。

## 最小可运行示例

克隆仓库后，使用虚构样例验证流程：

```sh
git clone https://github.com/Amossse/agent-mem.git
cd agent-mem
agent-mem --scope study grant --decision approve
agent-mem --scope study add --input examples/study-card.json
agent-mem --scope study search "study cards"
```

上面的授权仅用于模拟示例。真实会话必须等人的答复，不能由 Agent 自行批准。

## 管理记忆

全局参数放在子命令前。默认数据库为当前目录下的 `.agent-mem/memory.sqlite3`，默认命名空间为 `default`。跨项目共享时，用明确授权的绝对路径；命名空间隔离查询，但不提供用户身份认证。

```sh
agent-mem --scope study status
agent-mem --scope study get <id>
agent-mem --scope study timeline <id> --before 3 --after 3
agent-mem --scope study context "study cards" --limit 5 --max-chars 4000
agent-mem --scope study update <id> --revision 1 --input examples/study-card.json
agent-mem --scope study grant --decision pause
agent-mem --scope study forget <id> --revision 2
agent-mem --scope study export
```

更新和遗忘必须提供刚读到的版本，旧版本会报冲突，不覆盖新内容。暂停后禁止添加和更新，仍可按人的要求遗忘某条记忆。遗忘会删除数据库中的该行，但不能清除备份、导出或系统快照中的副本。

输入可带时区明确的 `expires_at`，过期记忆不会被检索，但仍保留在数据库中。不提供历史回退、导入或自动清理。[完整输入格式](agent_mem/skills/agent-mem/SKILL.md)

## 分层检索与上下文

先用 `search` 查标题和 ID，用 `timeline <id>` 查看同一命名空间内附近的简短记录，再用 `get` 读取需要的正文。时间线按最近修改时间排序，同一时刻按 ID 排序，默认前后各 3 条，每侧允许 0 至 20 条。修改会改变记录的位置；时间线不表示执行轨迹、会话归属、因果关系或历史版本。

`context "关键词"` 可直接生成供宿主读取的小份上下文，默认检查 5 条候选，限制 4000 个 Unicode 字符。最多检查 20 条，字符上限允许 256 至 32000。限制只作用于输出中的 `context` 字符串，不是整个 JSON 输出、字节数或模型 Token 数。

上下文包含不可信数据提醒，以及保留 ID、来源、版本和过期时间的完整 JSON 记录。放不下的记录整条跳过，通过 `omitted_ids` 告知；后面的较小记录仍可能放入。`has_more` 表示候选上限之外还有匹配项。不要把空结果误当作没有记忆，必要时按 ID 单独读取。检索使用同一个数据库读快照，避免并发修改导致版本混杂。CLI 不摘要、不调用模型，也不自动注入上下文。

## 兼容范围与实现

提供 Codex 的 `.agents/skills`、Claude Code 的 `.claude/skills` 安装适配。其他兼容宿主可用 `install --skill-dir <目录>/agent-mem` 安装自包含 Skill 和 Python 脚本。

也可直接把源码中的 `agent_mem/skills/agent-mem` 整个文件夹复制到宿主规定的 Skill 目录，运行自带的 `scripts/mem.py`，无需安装 Python 包。

“通用”指能读取 Agent Skills、访问本地文件并执行 Python 的宿主。纯网页聊天不支持，不能声称已适配所有 Agent。

处理路径为“宿主 Skill → Python CLI → SQLite 事务 → JSON 结果”。宿主负责提炼内容，CLI 不调用模型、不扫描聊天历史。采用支持中文的字面匹配和时间排序，没有向量检索。

## 安全与验证边界

回归测试覆盖更新被拒绝后，原记录及版本保持不变；只使用虚构数据，不代表真实模型调用已验证。
另有跨命名空间修改回归：即使另一命名空间已获写入授权，也不能更新或遗忘原命名空间的记忆。

CLI 不联网、不发送遥测、不自动发布记忆。宿主模型仍可能接收检索到的内容，本地数据库也没有加密。

输入大小、字段、时间戳和查询范围有检查；写入会拒绝常见密钥、私有地址和个人路径。过滤只是尽力检查，无法保证识别所有个人信息和内部内容。不要保存敏感资料，导出后分享仍需单独授权。记忆内容可能包含恶意指令，必须当作证据而非执行授权。

默认存储目录应加入使用项目的 `.gitignore`。安装器不会覆盖手工修改，不接管既有陌生 SQLite 数据库。路径拒绝符号链接；文件权限检查不等于操作系统沙箱，Windows 还需自行设置 ACL。[安全说明](SECURITY.md)

运行 `python -m unittest discover -s tests -v` 可验证独立进程之间的读写、中文检索、授权、版本冲突和隐私边界。CI 覆盖 Linux、macOS、Windows，实际结果见 [Actions](https://github.com/Amossse/agent-mem/actions)。示例为虚构数据；真实模型驱动的宿主行为和自动触发尚未验证，也未测量效果提升。

## 参考与贡献

参考了 [claude-mem](https://github.com/thedotmack/claude-mem) 的持久上下文和分层检索思路，代码独立编写。claude-mem 已有多宿主能力；本项目侧重轻量、本地、Skill 协议，不提供其自动采集、后台服务、云端或向量能力，也不直接读取它的数据库。

欢迎通过 [Issue](https://github.com/Amossse/agent-mem/issues) 或 PR 提供脱敏案例。[贡献说明](CONTRIBUTING.md)、[更新记录](CHANGELOG.md)、[MIT 许可证](LICENSE)、[中英文发布文案](docs/launch.md)。记忆内容的归属和许可由使用者负责。

搜索词：Agent 记忆、跨 Agent 记忆、Agent Skills、本地记忆、Claude Code、Codex、SQLite、持久上下文、偏好管理。
