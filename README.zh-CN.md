# Agent Mem

把值得保留的经验记一次，让另一个 Agent 也能查到。

一个通用 Agent Skill，加一个本地记忆管理 CLI。兼容的 Agent 共用 SQLite 文件和命名空间，保存偏好、事实、决策与操作经验。[English](README.md)

## 安装与使用

需要 Python 3.10+。运行时没有第三方依赖，不需要 API Key、后台服务或额外模型。通过 GitHub 安装，未发布到 PyPI：

```sh
uv tool install --python 3.11 git+https://github.com/Amossse/agent-mem.git@v0.1.0
cd your-project
agent-mem install --agent all
```

也可用 `pipx install git+https://github.com/Amossse/agent-mem.git@v0.1.0`。
安装后，新开 Codex 或 Claude Code 会话，调用 `$agent-mem` 或 `/agent-mem`，例如：

> 记住我的学习卡片每张只放一个问题，附一个简短例子。使用当前项目的本地记忆库，命名空间为 study；开启持续写入前先问我。

确认授权后，Agent 应保存简短记忆并返回 ID。换一个兼容 Agent，指定同一个数据库和命名空间即可查询。安装 Skill 不保证自动调用，也不会自动修改宿主的启动规则。

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
agent-mem --scope study update <id> --revision 1 --input examples/study-card.json
agent-mem --scope study grant --decision pause
agent-mem --scope study forget <id> --revision 2
agent-mem --scope study export
```

更新和遗忘必须提供刚读到的版本，旧版本会报冲突，不覆盖新内容。暂停后禁止添加和更新，仍可按人的要求遗忘某条记忆。遗忘会删除数据库中的该行，但不能清除备份、导出或系统快照中的副本。

输入可带时区明确的 `expires_at`，过期记忆不会被检索，但仍保留在数据库中。首版不提供历史回退、导入或自动清理。[完整输入格式](agent_mem/skills/agent-mem/SKILL.md)

## 兼容范围与实现

提供 Codex 的 `.agents/skills`、Claude Code 的 `.claude/skills` 安装适配。其他兼容宿主可用 `install --skill-dir <目录>/agent-mem` 安装自包含 Skill 和 Python 脚本。

“通用”指能读取 Agent Skills、访问本地文件并执行 Python 的宿主。纯网页聊天不支持，不能声称已适配所有 Agent。

处理路径为“宿主 Skill → Python CLI → SQLite 事务 → JSON 结果”。宿主负责提炼内容，CLI 不调用模型、不扫描聊天历史。检索先返回 ID 和标题，再读取选中的完整记录；采用支持中文的字面匹配和时间排序，没有向量检索。

## 安全与验证边界

CLI 不联网、不发送遥测、不自动发布记忆。宿主模型仍可能接收检索到的内容，本地数据库也没有加密。

输入大小、字段、时间戳和查询范围有检查；写入会拒绝常见密钥、私有地址和个人路径。过滤只是尽力检查，无法保证识别所有个人信息和内部内容。不要保存敏感资料，导出后分享仍需单独授权。记忆内容可能包含恶意指令，必须当作证据而非执行授权。

默认存储目录应加入使用项目的 `.gitignore`。安装器不会覆盖手工修改，不接管既有陌生 SQLite 数据库。路径拒绝符号链接；文件权限检查不等于操作系统沙箱，Windows 还需自行设置 ACL。[安全说明](SECURITY.md)

运行 `python -m unittest discover -s tests -v` 可验证独立进程之间的读写、中文检索、授权、版本冲突和隐私边界。CI 覆盖 Linux、macOS、Windows，实际结果见 [Actions](https://github.com/Amossse/agent-mem/actions)。示例为虚构数据；真实模型驱动的宿主行为和自动触发尚未验证，也未测量效果提升。

## 参考与贡献

参考了 [claude-mem](https://github.com/thedotmack/claude-mem) 的持久上下文和分层检索思路，代码独立编写。claude-mem 已有多宿主能力；本项目侧重轻量、本地、Skill 协议，不提供其自动采集、后台服务、云端或向量能力，也不直接读取它的数据库。

欢迎通过 [Issue](https://github.com/Amossse/agent-mem/issues) 或 PR 提供脱敏案例。[贡献说明](CONTRIBUTING.md)、[更新记录](CHANGELOG.md)、[MIT 许可证](LICENSE)、[中英文发布文案](docs/launch.md)。记忆内容的归属和许可由使用者负责。

搜索词：Agent 记忆、跨 Agent 记忆、Agent Skills、本地记忆、Claude Code、Codex、SQLite、持久上下文、偏好管理。
