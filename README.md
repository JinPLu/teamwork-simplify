# Teamwork

[Codex](CODEX.md) · [Claude Code](CLAUDE.md) · [Cursor](CURSOR.md)

Teamwork 帮你复用跨项目的协作偏好，让重要决定在后续工作中保持准确。
它包含一个用于方向讨论与复杂计划的 Skill、一份常驻工作约定，以及轻量项目上下文。

Codex 和 Claude Code 已经能够访谈、规划、执行和记忆。Teamwork 把你反复强调的
取舍方式与工程偏好组织成可复用的内容，减少重新解释和纠偏。
当前默认约定面向作者的跨项目工作；其中的具体代码约束是个人选择，安装前可阅读
[常驻策略](policy/teamwork-global.md)，判断是否适合自己的项目。

## 使用效果

清晰任务，例如“把这个按钮文字改成导出”，可以直接交给宿主执行。
需要共同选择方向或形成复杂计划时，可点名 `teamwork-collaborate`：

> 我们应先扩功能，还是先解决导出性能？先看现有数据，给我建议。

讨论后的决定可以是：

> 先解决性能，不改变 API，也不增加兼容分支。

后续计划据此说明可观察的结果，例如“相同数据导出耗时下降，现有调用不变”。
下一次工作能通过项目入口找到这个决定及其理由，减少再次询问是否修改 API。
实验数据、调查结论也可以留下可读记录，不必为一次对话搭建完整文档流程。

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

初始化维护 AGENTS.md 的项目说明块、CLAUDE.md 的共享指令桥接与项目上下文入口。
已有入口内容保持不动；旧托管桥接中的索引自动导入会被移除。用户自行添加的索引导入
保持不动并给出说明。不预建分类目录，也不迁移旧记录。

`doctor` 只读检查安装内容、托管块、入口与本地文档链接，不审查文档写作格式。
不带 `--project` 时会发现本机 Teamwork 项目；`--json` 输出结构化报告。
未启用的宿主无需补装；Cursor 策略的实际生效情况需要在 Cursor 中查看。

项目记录保存在目录里，并不代表它们已经随 Git 分享。本仓库的对话记录与本机索引
不纳入版本管理；公开说明使用上面的自包含示例，不发布历史对话。

[参与贡献](CONTRIBUTING.md) · [MIT 许可证](LICENSE)
