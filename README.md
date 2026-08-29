# Teamwork

<p align="center">
  <a href="CODEX.md">Codex</a> ·
  <a href="CURSOR.md">Cursor</a> ·
  <a href="CLAUDE.md">Claude Code</a>
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
确认方向、再拆出可以并行的工作、派给独立的执行面、最后把结果整合验证"
这一整条链路。Teamwork 只装这一条方法，加三个可选角色去执行拆分出来的
工作，再加一套按 kind 分类的文档记住这条链路上真正需要跨会话复用的东西。

## 三层：规则住在哪里，由谁读到它决定

Teamwork 把规则分放进三个物理上不同的层，原因不是风格选择，而是"谁会
读到这条规则"直接决定它能不能生效：

- **常驻层**（`policy/teamwork-global.md`）。安装器把这份文件整篇写进
  Codex / Cursor / Claude Code 三个宿主各自的全局指令文件，每个项目的
  每个线程都会读到它，不管这次对话有没有提到 Teamwork。这份"每线程都要
  付费"的成本决定了它只能装动手前就必须成立的规则；任何项目专属或任务
  专属的细节放进来，都是让用不到它的线程白白买单。文档怎么读回项目已有
  状态、何时落盘、落哪个 kind、身份怎么判断、路径怎么复用、文档长什么
  样、连一份可复制的最小骨架——这份最小完整的契约整份住在这里，因为它
  必须在原生交互（不先点名 Skill）里同样成立，只有常驻层能做到这一点。
- **按需层**（`skills/teamwork-collaborate/SKILL.md`）。Skill 有两部分、
  两种成本：`description` 常驻在上下文里用于路由，宿主靠它判断当前请求
  是否匹配；正文——真正的方法——只在触发匹配、宿主把文件拉进来时才加载。
  这意味着"这类任务具体怎么做"的方法只能放在正文里；把一条通用约束写进
  Skill 正文，等于没写——它在 Skill 没被触发的大多数时间里根本不生效。
  落盘契约本身不在这里复述：正文只指向常驻层那份契约，`references/*.md`
  提供该契约要求的文档骨架（frontmatter 字段、顶部综合、追加式历史），
  在手边时套用对应的一份。
- **项目层**（项目自己 `AGENTS.md` 的 Teamwork 托管块）。承载项目作用域
  的补充与覆盖——例如这个项目的 `docs/teamwork/` 落盘根目录在哪。落盘
  契约本身的唯一所有者是常驻层，这一层只加项目专属细节，不复述契约。

规则放错层的后果是双向的：放进常驻层的任务专用规则，让每一个用不到它的
线程都要为它付出上下文成本；放进按需层的通用约束，在 Skill 没加载的时候
就等于不存在。

**处置规则**：当宿主自己获得了能覆盖某个 Teamwork 契约的原生能力时，
对应的 Teamwork 面被删除，而不是留下来跟原生能力并存。这也是上一代
产品从八个 Skill（其中五个跟宿主原生模式重复）收缩成现在这一个 Skill
的依据——不是把旧实现弃置在原地，而是真的删掉。

## 一分钟安装

```bash
git clone https://github.com/JinPLu/teamwork-simplify.git
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

每个安装 target（`codex` / `cursor` / `claude` / `all`，以及 `init-project`）
都会把这次运行所在的 checkout 写进 `~/.teamwork/install.json`：覆盖
`root`（当前 checkout 的绝对路径）与 `version`，并把这次装的宿主并入已
记录的 `hosts` 列表（`init-project` 不带宿主，不会新增或删除任何宿主
记录，只刷新 `root`/`version`）。只有 `./install.sh update` 会**读**这份
指针：它按指针记录的 `root` 依次对指针记录的**每一个**宿主重新执行
`./install.sh <host>`，和你运行 `update` 时人在哪个目录无关；指针缺失、
不是合法 JSON、记录的 `hosts` 为空、或记录的 checkout 已不可用（缺
`VERSION`、`skills/`、`install.sh` 三者之一）时，`update` 直接失败退出，
不会退回当前目录、也不会改写指针。`init-project` 只写指针，不读它。

## 一个 Skill 能做什么

Teamwork 只有一个公开 Skill：`teamwork-collaborate`。它把一次需要共同判断
方向的工作，从讨论一路带到可验证的结果：

1. **讨论**：列出真正有意义的选项和权衡，不为了流程而提问。
2. **方向**：收敛到一个你愿意采用、且已经确认的方向。
3. **可执行计划**：把方向拆成有依赖顺序、可验证、有停止条件的步骤。
4. **拆并行线**：把彼此独立的步骤分成可以同时推进的线，交给宿主自己的
   并行执行面去跑；宿主没有这样的原生面时，才落到可选的 Worker 角色兜底。
5. **整合验证**：收回结果，检查真实证据，决定进入主线还是回到讨论。

在 Codex 里用 `$teamwork-collaborate` 点名它；在 Cursor / Claude Code 里用
`/teamwork-collaborate`。目标和边界已经清楚的改动不需要它，直接说结果
即可。

## 三个可选角色

Skill 拆出的工作由三个边界化角色去做，都是可选的，缺席不会卡住主线：

| 角色 | 做什么 |
| --- | --- |
| Challenger | 对已成形的方向或计划找真实反例和被忽略的代价，不负责生成新方案。 |
| Worker | 在给定的写入范围内完成一条并行线的具体工作，返回结果与证据；宿主有自己的并行执行面时优先用那个，Worker 是没有原生面时的兜底。 |
| Writer | 把方法 owner 已经确认的结果写成 `docs/teamwork/<kind>/` 下的 Markdown，不改变事实或结论；写不了就返回 `no-write` 和确切缺口，由 Root 报告未交付的路径。 |

Root 只在并行调查、独立判断或分工确实有用时才派发；handoff 只带五个
字段：**目标（objective）、负责范围（owned scope）、已确定约束
（settled constraints）、已有证据（available evidence）、期望返回
（requested return）**。

## 可读文档

新会话或新一轮工作开始前，先读 `docs/teamwork/README.md`——上半是这个
项目现在的状态，下半是每份文档一行的索引；跟着索引打开真正相关的那
几份，不必逐个目录翻找或逐份读 frontmatter。

落盘不再等你先说"接受"：本轮一旦产出了下一个会话还用得到、且离开这
次对话就没法复原的东西，Root 就在同一响应周期把纯 Markdown 写入
`docs/teamwork/<kind>/`，并顺手刷新索引里对应的一行；进入宿主界面本身
不会落盘，也不必先点名 Skill；哪些结论不值得落盘，同一节另有定义。
Writer 只在不耽误写入时帮忙。每份文档同时保留一份**当前综合**和按时
间追加的**历史**，既方便快速阅读，也不会抹掉结论如何变化。

kind 是闭集，不会新造额外 kind，也不会在 `docs/teamwork/` 根目录直接落盘；
闭集具体包含哪些类目由常驻层契约定义。具体何时落盘、落哪个 kind、身份
怎么判断、路径怎么复用、文档长什么样，这份最小完整的落盘契约唯一的
所有者是常驻层 `policy/teamwork-global.md`；
目标项目自己 `AGENTS.md` 里的 Teamwork 托管块只加项目专属细节，不复述
契约。文档不依赖 Case、schema、JSON 索引或迁移状态；没有可复用的变化时，
也不必为了流程去创建文档。这套读取侧与落盘契约落到真实项目里长什么样，
见这个仓库自己的 [`docs/teamwork/README.md`](docs/teamwork/README.md)。

## 项目初始化

只给一个项目加入轻量 Teamwork 说明，不创建任何数据库或运行时状态：

```bash
./install.sh --project-root /absolute/project/path init-project
```

它只添加或刷新三样东西：`AGENTS.md` 的 managed block、一个很小的
`CLAUDE.md` bridge（Claude Code 读 `CLAUDE.md` 不读 `AGENTS.md`），
以及这个项目的读取侧入口 `docs/teamwork/README.md`。不创建任何空的 kind
目录，已存在的 `docs/teamwork/README.md` 完全不动。

## 继续了解

- [Codex](CODEX.md) / [Cursor](CURSOR.md) / [Claude Code](CLAUDE.md)：各宿主
  的安装方式与原生能力映射。
- [参与贡献](CONTRIBUTING.md)：canonical owner 与验证命令。
- [`docs/teamwork/README.md`](docs/teamwork/README.md)：这个仓库自己的
  项目当前状态与文档索引——读取侧契约在真实项目里的样子。

许可证：[MIT](LICENSE)
