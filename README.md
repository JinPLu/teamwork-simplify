# Teamwork

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="CODEX.md">Codex</a> ·
  <a href="docs/architecture.md">架构</a>
</p>

---

Teamwork 是一层极薄的补充：Codex / Cursor / Claude Code 已经能做的事（原生
Plan、原生问答、原生 Debug、原生代码复查）它不重复；只补两样宿主本身没有的
东西——一份跨项目都成立的常驻工作规则，和一个把"先讨论方向、再定计划、
再拆分执行"这件事做完整的方法。

## 解决什么问题

清楚、已授权的改动应该直接做，不需要先走一套流程。真正缺的是另一件事：
当方向还没定、需要几个人（或几条并行线）一起把一个模糊目标收敛成一份
可执行计划时，原生的 Plan 模式通常只管"写计划"，不管"先讨论选项、
确认方向、再拆出可以并行的工作、派给独立的 Worker、最后把结果整合验证"
这一整条链路。Teamwork 只装这一条方法，加三个可选角色去执行拆分出来的
工作，再加一套四类文档记住这条链路上真正需要跨会话复用的东西。

## 一分钟安装

```bash
git clone <this-repository-url>
cd teamwork-simplify
./install.sh claude   # 或 codex / cursor-policy
```

- `./install.sh codex` 把 Skill、三个角色模板和常驻政策安装进 Codex
  （政策写入 `~/.codex/AGENTS.md`）。
- `./install.sh claude` 把同样的内容安装进 Claude Code（政策写入
  `~/.claude/CLAUDE.md`）。
- `./install.sh cursor` 安装 Skill 与角色；`./install.sh cursor-policy`
  单独打印（并尝试复制）常驻政策文本，因为 Cursor 的 User Rules 是它自己
  设置里的一份文本，不是安装器能直接写的文件——这一步需要手动粘贴到
  Settings -> Rules -> User Rules。

## 一个 Skill 能做什么

Teamwork 只有一个公开 Skill：`teamwork-collaborate`。它把一次需要共同判断
方向的工作，从讨论一路带到可验证的结果：

1. **讨论**：列出真正有意义的选项和权衡，不为了流程而提问。
2. **方向**：收敛到一个你愿意采用、且已经确认的方向。
3. **可执行计划**：把方向拆成有依赖顺序、可验证、有停止条件的步骤。
4. **拆并行线**：把彼此独立的步骤分成可以同时推进的线。
5. **Worker 派发**：把每条线的边界化任务交给一个 Worker 去做。
6. **整合验证**：收回结果，检查真实证据，决定进入主线还是回到讨论。

在 Codex 里用 `$teamwork-collaborate` 点名它；在 Cursor / Claude Code 里用
`/teamwork-collaborate`。目标和边界已经清楚的改动不需要它，直接说结果
即可。

## 三个可选角色

Skill 拆出的工作由三个边界化角色去做，都是可选的，缺席不会卡住主线：

| 角色 | 做什么 |
| --- | --- |
| Challenger | 对已成形的方向或计划找真实反例和被忽略的代价，不负责生成新方案。 |
| Worker | 在给定的写入范围内完成一条并行线的具体工作，返回结果与证据。 |
| Writer | 把方法 owner 已经确认的结果写成 `docs/teamwork/<kind>/` 下的 Markdown，不改变事实或结论；写不了就返回 `no-write` 和确切缺口，由 Root 报告未交付的路径。 |

Root 只在并行调查、独立判断或分工确实有用时才派发；handoff 只带五个
字段：目标、负责范围、已确定约束、已有证据、期望返回。

## 四类可读文档

<!-- BEGIN GENERATED: persistence-zh -->
当原生交互或 `teamwork-collaborate` 到达可复用语义结果、且你已经接受该结果时，Root 在同一响应周期把纯 Markdown 写入 `docs/teamwork/<kind>/`；进入宿主界面本身不会落盘，也不必先点名 Skill。Writer 只在不耽误写入时帮忙。每份文档同时保留一份**当前综合**和按时间追加的**历史**，既方便快速阅读，也不会抹掉结论如何变化。默认路径为 `docs/teamwork/<kind>/<slug>.md`，同一稳定身份复用已有路径。

| 文档 | 它记录什么 |
| --- | --- |
| 💬 Discussion | 选项、权衡、已定选择、被否决的方案与仍待决定的问题 |
| 📝 Plan | 已选方向的可执行步骤、依赖、并行线与 Worker 分派、验证和停止条件 |
| 📌 Record | 可跨会话复用的结果、结论与阻塞 |
| 🧪 Experiment | 一次试验的说法、设置、实际运行、结果与结论 |
<!-- END GENERATED: persistence-zh -->

文档不依赖 Case、schema、JSON 索引或迁移状态；没有可复用的变化时，也不必
为了流程去创建文档。详见 [`docs/teamwork/README.md`](docs/teamwork/README.md)。

## 项目初始化

只给一个项目加入轻量 Teamwork 说明，不创建任何数据库或运行时状态：

```bash
./install.sh --project-root /absolute/project/path init-project
```

它只添加或刷新一个 `AGENTS.md` managed block（Claude Code 读 `CLAUDE.md`
不读 `AGENTS.md`，所以还会补一个一行的 `@AGENTS.md` import）。

## 继续了解

- [架构](docs/architecture.md)：常驻政策与按需 Skill 这两层为什么物理上必须
  分开，以及源所有权、Agent handoff、四类文档的闭集。
- [Codex](CODEX.md) / [Cursor](CURSOR.md) / [Claude Code](CLAUDE.md)：各宿主
  的安装方式与原生能力映射。
- [参与贡献](CONTRIBUTING.md)：canonical owner 与验证命令。
- [`docs/teamwork/README.md`](docs/teamwork/README.md)：四类文档各自维护
  什么、建档粒度、frontmatter 约定。

许可证：[MIT](LICENSE)
