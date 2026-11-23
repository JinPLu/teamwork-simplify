# Teamwork

Teamwork 面向跨会话、跨宿主长周期协作的科研与工程项目，只做现代 Agent 宿主仍容易漂移的三件事：**按因果机制展开研究判断、让实验结论严格对准对象与条件、把关键决定收敛在一屏可读的活入口上**。

Antigravity、Codex、Claude Code 与 Cursor 已经原生具备规划、工具调用、子代理编排与权限控制。Teamwork 的每一部分都按同一顺序取舍——**先问是否必要，再求简洁，再放手发挥宿主原生能力，最终落脚到更低负担的人机交互**。它不安装子代理、Hook、流程脚手架或项目样板块，仅包含一份常驻策略与一个按需加载的决策方法 Skill。

## 协作体验

边界清晰的任务直接交给宿主原生完成，零额外仪式。遇到方向选择、竞争性解释排查、方案取舍或复杂多步规划时，宿主按语义自动加载或由你点名 `teamwork-collaborate`：

- **直接判断与因果推演**：开头直给实质判断与推荐；复杂研究与设计讨论按“现象 → 原因与机制 → 具体改法 → 验证方式”结合项目实例展开，适合时用表格或示意图呈现；论文与写作修改先讲清修改点再给出完整连贯的可用段落，不把需要推理的讨论压成干瘪结论、状态清单或机械模板。
- **先定判据再跑实验**：选择取决于实验或排查结果时，先设计最小判别检查，并事先写明“观测到什么结果选哪个分支、什么结果证伪假设”，让结果直接落到对应决策而非事后找解释。
- **轻量证据边界**：保持独立研究判断，不做空泛赞美或未经证实的夸大断言；区分实测事实、推断与提案，把对象、版本、条件与来源简洁附在对应论点旁，缺口直接标为缺口，既不拿其他配置的数据顶替，也不让重复免责声明或无关路径挤占主体分析。
- **局部质疑不翻全局盘**：当你反驳某一点或新结果推翻旧前提时，先点明争议前提，只重审依赖它的结论与计划分支，无关决定保持不动；研究目标变更与重度资源投入（付费接口、多卡运行、预计超过约 10 个代理或 1 小时的并发任务）始终由你拍板，提及收缩或配额立即停止。
- **零初始化与一屏收敛**：项目无需预跑初始化命令。需要跨会话保留结论时，优先遵循项目自有说明（如 `AGENTS.md`），未指定时按需使用 `docs/teamwork/README.md`：入口与主题顶部保持约一屏的当前有效判断、活跃问题与带日期的用户拍板理由并**原地改写**（淘汰方案折成一行保留原因与重开条件）；实验数字归单一读数页持有，进程号、租约与流水留给运行日志。

## 架构分工

- **[常驻策略](policy/teamwork-global.md)**：写入宿主全局规则文件的 `TEAMWORK_GLOBAL` 托管块，承载跨项目表达方式、证据纪律、资源知情边界与项目接续约定；托管块之外你的自有规则逐字节保留。
- **[协作方法 Skill](skills/teamwork-collaborate/SKILL.md)**：安装至宿主全局 Skill 目录，仅在竞争假设判别、方向权衡与从已定分支生成计划时加载（在 Antigravity 中与宿主原生多代理并发命令 `/teamwork` 职责正交，互不冲突）。

## 安装与维护

```bash
git clone https://github.com/JinPLu/teamwork-simplify.git
cd teamwork-simplify

# 安装到指定宿主（支持多宿主同装，或使用 all 全部安装）
./install.sh agy codex
./install.sh all

# 本地开发模式：使用软链直接跟踪当前仓库
./install.sh --link all

# 一键刷新本机已启用 Teamwork 的全部宿主（自动保持各自 copy / link 模式）
./install.sh refresh

# 卸载指定宿主（仅移除 Teamwork 的 Skill 与策略托管块，保留你的其他规则）
./install.sh uninstall claude
```

各宿主的安装落点：

| 宿主 | 目标名 | Skill 目录 | 全局策略位置 |
| :--- | :--- | :--- | :--- |
| Antigravity | `antigravity` / `agy` | `~/.gemini/config/skills/` | `~/.gemini/GEMINI.md` |
| Codex | `codex` | `~/.agents/skills/` | `$CODEX_HOME/AGENTS.md`（默认 `~/.codex/AGENTS.md`） |
| Claude Code | `claude` | `~/.claude/skills/` | `~/.claude/CLAUDE.md` |
| Cursor | `cursor` | `~/.cursor/skills/` | 运行 `./install.sh policy --clipboard` 后粘贴至 `Settings → Rules → User Rules` |

如目标目录已存在未带 Teamwork 标记的同名 `teamwork-collaborate`，安装器默认拒绝覆盖以保护自定义内容；确认接管时附加 `--force`。

## 诊断与校验

```bash
# 只读检查本机各宿主安装一致性，以及 ~/Documents 下项目的入口链接可达性
./install.sh doctor
./install.sh doctor --project /path/to/project --json

# 运行行为测试套件
./scripts/validate.sh
```

`doctor` 仅做只读结构检查：核对已启用宿主的 Skill 与全局策略块是否与当前仓库一致，并检查项目 `docs/teamwork/README.md` 中的本地文档链接是否有效（核心文档断链报 `error`，外部或已清理的运行产物目录报 `warn`）。

[MIT License](LICENSE)
