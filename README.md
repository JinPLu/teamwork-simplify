# Teamwork

面向跨会话、跨宿主科研与工程协作的轻量工具箱。现代 Agent 宿主（Antigravity、Codex、Claude Code、Cursor）已原生具备规划、工具调用、子代理与权限管理，Teamwork 只补齐它们仍易漂移的协作约束，不安装子代理、Hook 或项目样板块。

仓库内每一项设计均按同一顺序取舍：**必要 → 简洁 → 原生能力 → 人机交互**。

## 核心效果

边界清晰的任务直接交给宿主原生完成，零额外仪式；需要长周期协作时提供三项可感知能力：

- **先全局后局部的决策与验证**：遇方向权衡、竞争假设或复杂规划时，先锁定上游目标与阻塞前提，再落到局部方案与可证伪的最小判别实验；中途质疑只重审依赖分支，不推翻无关已定结论。
- **零初始化的跨宿主项目记忆**：无需预跑项目初始化，按需接续项目既有知识入口（默认 `docs/teamwork/README.md`），以原地改写维持一屏可读的活视图，保留关键用户原话与单一数值来源。
- **清晰的人机权责与证据边界**：事实、推断与提案分明，证据缺口直白标出而不阻断已授权工作；代码保持单一清晰主路径，目标变更与重度资源投入始终由你拍板。

## 双文件架构

- **[`policy/teamwork-global.md`](policy/teamwork-global.md)**：常驻策略，写入宿主全局规则文件的 `TEAMWORK_GLOBAL` 托管块（块外自有规则逐字节保留）。承载在 Skill 加载之前、以及长会话上下文压缩（compaction）之后仍须保持生效的全局偏好与项目记忆不变量。
- **[`skills/teamwork-collaborate/SKILL.md`](skills/teamwork-collaborate/SKILL.md)**：单文件协作 Skill，安装至宿主全局 Skill 目录，仅在需要多轮方向权衡、假设判别或决策转计划时按需加载（在 Antigravity 中与原生并发命令 `/teamwork` 职责正交）。

## 安装与维护

```bash
git clone https://github.com/JinPLu/teamwork-simplify.git
cd teamwork-simplify

# 安装到指定宿主或全部四宿主（--link 使用软链跟踪本仓库）
./install.sh agy codex
./install.sh --link all

# 刷新本机已启用的宿主（保持各自 copy / link 模式）
./install.sh refresh

# 卸载指定宿主（仅移除 Teamwork 的 Skill 与策略托管块）
./install.sh uninstall claude

# 输出或复制全局策略块（用于手动粘贴至 Cursor User Rules）
./install.sh policy --clipboard
```

| 宿主 | 目标名 | Skill 目录 | 全局策略位置 |
| :--- | :--- | :--- | :--- |
| Antigravity | `antigravity` / `agy` | `~/.gemini/config/skills/` | `~/.gemini/GEMINI.md` |
| Codex | `codex` | `~/.agents/skills/` | `$CODEX_HOME/AGENTS.md`（默认 `~/.codex/AGENTS.md`） |
| Claude Code | `claude` | `~/.claude/skills/` | `~/.claude/CLAUDE.md` |
| Cursor | `cursor` | `~/.cursor/skills/` | 运行 `./install.sh policy --clipboard` 后粘贴至 `Settings → Rules → User Rules` |

目标目录若存在未带 Teamwork 标记的同名 `teamwork-collaborate`，安装器默认拒绝覆盖；确认接管时附加 `--force`。

## 诊断与校验

```bash
# 只读检查各宿主安装一致性（若当前目录存在 docs/teamwork/ 会一并检查其入口链接）
./install.sh doctor

# 显式检查任意项目的 docs/teamwork/ 入口链接（支持 --json）
./install.sh doctor --project /path/to/project --json

# 运行行为测试与校验套件
./scripts/validate.sh
```

`doctor` 为纯只读诊断：核对各已启用宿主的 Skill 与全局策略块是否与当前仓库一致，并在检测到 `docs/teamwork/` 时校验 `README.md` 中的本地 Markdown 链接可达性。

[MIT License](LICENSE)
