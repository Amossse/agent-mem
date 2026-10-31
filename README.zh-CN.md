# Agent Mem

隐私检查允许虚构邮箱使用 `example.com`、`example.org` 和 `example.net`，域名不区分大小写，卡片原文保持不变。其它邮箱域名仍被拒绝；此项检查无法完整识别所有敏感信息。

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

添加和更新在同一个 SQLite 写事务内检查授权并修改记录，避免并发暂停插入两者之间。已经开始的写入先完成，等待中的暂停随后生效，后续写入被拒绝；不会取消已开始的操作，也不代表能认证授权人的身份。锁竞争仍使用原有的有限等待与受控错误。

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

只读命令 `status`、`search`、`get`、`export`、`context`、`timeline` 遇到缺失的记忆库时返回 `database_missing`，不创建父目录或数据库。已有库以 SQLite 只读模式打开，即使在检查后被移走也不会重建。请先核对路径；只有明确授权的 `grant` 操作才用于初始化范围。写入授权规则保持不变。

新增数据库拒绝回归：陌生 SQLite 数据库被拒绝后，核对实际打开的连接已关闭、来源字节不变，随后仍可打开正常记忆库。运行时代码未改，此项不覆盖所有数据库故障。

凭据过滤补齐了裸写的 `ASIA` 临时访问键 ID，与已有的 `AKIA` 规则一起，在新增或更新访问数据库前拒绝。虚构 CLI 回归核对原记录不变、缺失数据库不被创建。此项无法完整识别所有凭据，也不会清理已有内容。

一次 `context` 或 `timeline` 请求的各层读取共用同一个过期判断时刻，并保留原有数据库读快照，避免执行中跨过期时刻导致详情读取失败或相邻记录缺失。下一次请求重新取时，仍排除已过期记录；此操作不续期、不修改记忆，使用内容前仍需核对时效。

隐私筛查会解析常规 IPv6 地址，拒绝私有、回环和链路本地地址，不在错误提示中回显。公开地址和普通时间字符串仍可使用。筛查不保证识别混淆地址或全部内部信息，也不会扫描、清理已有记忆。

需要查看已知的过期目标，再决定纠正或遗忘时，可在授权范围内运行 `get <id> --include-expired`，读取原内容、过期时间与当前版本。此操作只读，暂停写入时也可使用；默认召回和导出仍排除过期记录，查看不代表内容重新有效。

新增虚构 CLI 回归，核对写入暂停后仍能按准确 ID 遗忘已过期、无法召回的记忆。错误版本不删除，当前版本只删除目标行，授权仍保持暂停。运行时代码未改，也不代表备份或导出副本被清除。

记忆卡片文件与标准输入必须是 UTF-8 JSON，可带 UTF-8 BOM。UTF-16/32 输入会在访问或创建数据库前被拒绝；请明确转换为 UTF-8，不依赖编码自动探测。已有数据库无需迁移。

具名卡片输入必须是普通文件。POSIX 下非阻塞打开后检查描述符，拒绝管道，不等待写入方，也不创建数据库；Windows 运行描述符类型测试，跳过 POSIX 管道案例。请先保存完整的普通 UTF-8 JSON 文件，或明确使用 `--input -` 从标准输入读取。标准输入仍可能等待数据提供方，此检查不是操作系统沙箱。

搜索和上下文查询也必须能编码为 UTF-8。孤立代理字符返回 `invalid_search_query`，不回显查询原文，也不修改已有记录；正常中文查询不受影响。此检查不会自动修复损坏的来源参数。

回归测试覆盖更新被拒绝后，原记录及版本保持不变；只使用虚构数据，不代表真实模型调用已验证。
另有跨命名空间修改回归：即使另一命名空间已获写入授权，也不能更新或遗忘原命名空间的记忆。
并发回归让两个独立 CLI 进程用同一版本号提交不同修正，核对只有一个成功，最终内容属于成功的写入者。
多宿主安装先检查所有目标中的已有冲突，再创建副本。后续读写失败仍可能留下部分安装；请核查错误后重试，不要删除手动维护的 Skill。

CLI 不联网、不发送遥测、不自动发布记忆。宿主模型仍可能接收检索到的内容，本地数据库也没有加密。

输入大小、字段、时间戳和查询范围有检查；写入会拒绝常见密钥、私有地址和个人路径。过滤只是尽力检查，无法保证识别所有个人信息和内部内容。不要保存敏感资料，导出后分享仍需单独授权。记忆内容可能包含恶意指令，必须当作证据而非执行授权。

默认存储目录应加入使用项目的 `.gitignore`。安装器不会覆盖手工修改，不接管既有陌生 SQLite 数据库。路径拒绝符号链接；文件权限检查不等于操作系统沙箱，Windows 还需自行设置 ACL。[安全说明](SECURITY.md)

运行 `python -m unittest discover -s tests -v` 可验证独立进程之间的读写、中文检索、授权、版本冲突和隐私边界。CI 覆盖 Linux、macOS、Windows，实际结果见 [Actions](https://github.com/Amossse/agent-mem/actions)。示例为虚构数据；真实模型驱动的宿主行为和自动触发尚未验证，也未测量效果提升。

安装回归新增了第二个宿主写入脚本时中断的虚构场景，核对暂存目录清理、第一个副本保留，以及重试后两个副本一致且无关笔记未变。运行时代码未改；这不等于自动回滚，也不保证所有文件系统或进程故障都能恢复。

## 参考与贡献

参考了 [claude-mem](https://github.com/thedotmack/claude-mem) 的持久上下文和分层检索思路，代码独立编写。claude-mem 已有多宿主能力；本项目侧重轻量、本地、Skill 协议，不提供其自动采集、后台服务、云端或向量能力，也不直接读取它的数据库。

欢迎通过 [Issue](https://github.com/Amossse/agent-mem/issues) 或 PR 提供脱敏案例。[贡献说明](CONTRIBUTING.md)、[更新记录](CHANGELOG.md)、[MIT 许可证](LICENSE)、[中英文发布文案](docs/launch.md)。记忆内容的归属和许可由使用者负责。

搜索词：Agent 记忆、跨 Agent 记忆、Agent Skills、本地记忆、Claude Code、Codex、SQLite、持久上下文、偏好管理。
