# Teamwork

[Codex](CODEX.md) · [Claude Code](CLAUDE.md) · [Cursor](CURSOR.md)

Teamwork 增强长期项目维护：长程讨论能接续，项目文档保持当前判断，
工程约束帮助减少不断累积的重复实现和维护负担。
它包含一个用于方向讨论与复杂计划的 Skill、一份常驻工作约定，以及轻量项目上下文。

Codex 和 Claude Code 已经能够访谈、规划、执行和记忆。Teamwork 把你反复强调的
取舍方式与工程偏好组织成可复用的内容，减少重新解释和纠偏。
当前默认约定面向作者的跨项目工作；其中的具体代码约束是个人选择，安装前可阅读
[常驻策略](policy/teamwork-global.md)，判断是否适合自己的项目。

> **本仓库接替已废弃的 [JinPLu/Teamwork](https://github.com/JinPLu/Teamwork)。**
> 旧版把研究、调试、计划、执行、复查拆成八个 Skill 和一组可选 Agent 角色，替宿主
> 搭出流程脚手架。Astra、Fable 5.1 这一代模型已经把这层脚手架吸收成原生能力，
> 再维护一套只会与宿主重复并互相冲突。因此本仓库不是旧版的续版，而是一次全面重构：
> 只保留一个 `teamwork-collaborate`、一份常驻策略和轻量项目上下文，流程、角色分工与
> 执行编排交回宿主。装过旧版的，从本仓库 checkout 运行下面的安装命令即可；确认属于
> Teamwork 的旧 Skill 与 Agent 角色会被一并移除，你自己的内容不动。

## 使用效果

清晰任务，例如“把这个按钮文字改成导出”，可以直接交给宿主执行。
需要共同选择方向或形成复杂计划时，可点名 `teamwork-collaborate`：

> 我们应先扩功能，还是先解决导出性能？先看现有数据，给我建议。

讨论后的决定可以是：

> 先解决性能，不改变 API，也不增加兼容分支。

后续计划据此说明可观察的结果，例如“相同数据导出耗时下降，现有调用不变”。
下一次工作能通过项目入口找到这个决定及其理由，减少再次询问是否修改 API。
实验数据、调查结论也可以留下可读记录，不必为一次对话搭建完整文档流程。

长讨论中，项目入口与主题文档保留整体目标、当前问题和仍未解决的分支。
你质疑一个设计后，下一轮接着解释或比较被改变的判断；形成计划时，能看见
哪些必要部分已覆盖、哪些仍待解决。代码或实验推翻旧前提时，相关结论与计划
随之更新。重复的代理解释可以压缩，重要原话、证据和决定变化仍可回查。
同一判断集中维护，减少每次接续重读历史或纠正多个副本的负担。
关键判断保留来源位置、版本和适用条件；证据改变时，使用它的计划和汇报也能跟进。
已有的笔记库和项目入口继续负责保存知识，冻结材料与追加式记录保留原件及更正。
这些是方法的预期收益，有限情境验收不能证明所有长期项目都已解决漂移问题。

## 三层如何分工

- **常驻策略**：安装进宿主全局指令文件，承载每次工作需要的个人约定与简短的
  项目上下文读写约定。它的成本由所有任务承担，因此保持精简。
- **按需 Skill**：匹配方向讨论或复杂计划时加载方法正文。清晰执行任务继续使用
  宿主原生能力；并行、工具调用和执行权限也由宿主负责。
- **项目说明**：通过项目指令文件声明本项目的上下文入口，并保留项目自己的约束。
  详细记录在需要时读取。

工作约定的权威来源是 [policy/teamwork-global.md](policy/teamwork-global.md)。
Skill 的参考文件提供可选示例。Teamwork 不安装 agents、hooks、调度系统或文档数据库。

## 安装与刷新

```bash
git clone https://github.com/JinPLu/teamwork-simplify.git
cd teamwork-simplify
./install.sh codex
# 或 ./install.sh claude
```

Codex 安装会写入用户 Skill 目录和全局 AGENTS.md 的 Teamwork 托管块；
Claude 安装会写入对应 Skill 目录和全局 CLAUDE.md 托管块。
刷新时从所需 checkout 再运行相同命令。默认复制；本地开发可选 `--link`。
安装器保护托管区域之外的用户内容，旧版本角色只在内容确认归属于 Teamwork 时清理。

Cursor 使用 `./install.sh cursor` 安装 Skill，再运行 `./install.sh cursor-policy`
取得策略文本，在 Settings → Rules → User Rules 中更新对应块。安装器不能读取该设置。

## 项目初始化与诊断

```bash
./install.sh --project-root /absolute/project/path init-project
./install.sh doctor --project /absolute/project/path
```

初始化只维护 AGENTS.md 的项目说明块和 CLAUDE.md 的共享指令桥接，不创建文档目录或空索引。
首次需要保存持久结果时，遵循项目已有的知识归属和入口；未指定时使用 `docs/teamwork/README.md`。
已有入口内容保持不动；旧托管桥接中的索引自动导入会被移除。用户自行添加的索引导入
保持不动并给出说明。不预建分类目录，也不迁移旧记录。

`doctor` 只读检查安装内容、托管块、入口与本地文档链接，不审查文档写作格式。
不带 `--project` 时会发现本机 Teamwork 项目；`--json` 输出结构化报告。
未启用的宿主无需补装；Cursor 策略的实际生效情况需要在 Cursor 中查看。

项目记录保存在目录里，并不代表它们已经随 Git 分享。本仓库的对话记录与本机索引
不纳入版本管理；公开说明使用上面的自包含示例，不发布历史对话。

[参与贡献](CONTRIBUTING.md) · [MIT 许可证](LICENSE)
