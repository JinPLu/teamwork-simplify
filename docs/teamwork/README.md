# Teamwork 项目文档

这是 teamwork-simplify 这个项目自己的读取侧入口：上半是项目现在的状态，
下半是磁盘上每份文档的一行索引。新会话或新一轮工作依赖这个项目已经
决定、得出结论或试过的东西时，先读这里，再跟着索引打开真正相关的那
几份，而不是逐个目录去翻、逐份读 frontmatter。

多少类文档、每类回答哪个问题、路径怎么复用、文档骨架长什么样、命中
同一身份时怎么追加历史——这份最小完整的契约唯一的所有者是常驻层
`policy/teamwork-global.md` 的 Project context 一节。下面两节只呈现这条
契约应用到这个项目之后的真实结果，不是另一份独立规则。

## 项目当前状态

- **刚完成**：[收缩到三样真实增量](plans/teamwork-drop-execution-surface-and-slim-delivery.md)。
  执行面（三个角色、拆线判定、handoff 契约、宿主并行面描述）整个还给 harness；
  交付机器里与产品无关的自维护机制（源指针、`update` target、plugin-runtime-root、
  SessionStart hook）一并下架。交付机器 4434 → 3391 行，产品:机器 从 1:11 到 1:8.3。
  随后按用户反馈纠正两处过度收缩：计划里要写下**启动工作的那一行**（走哪个面、
  哪些并行、按什么平衡模型），只是不冻结拆几条线和各线档位；模型平衡由规定式
  改为信任式一句「自己按速度、费用、效果平衡可调用的 model/effort」。
  49 条测试全绿，三宿主已装到真实 HOME，`doctor` GLOBAL 与本仓库均 0 error。
  **本轮改动未提交。**
- [契约重设计](plans/teamwork-contract-redesign.md) 的读取侧与判据部分已实施并提交
  （`b3ac77f` + `cd1abc8`）；其并行/编排部分已被上面那份推翻。
- [落盘兜底、配置自检与 guides/](plans/teamwork-persistence-fallback-and-config-doctor.md)
  仍是 active；doctor 的文档形状检查已由另一线程实现并提交（`63d77dd`）。
- 已废弃（status: superseded）：
  [落盘契约下沉到项目层](plans/teamwork-layer-fix-and-cleanup.md)——两条方向都被推翻。
- 已定方向、不再重开：
  [Teamwork 收缩为 teamwork-simplify](discussions/teamwork-shrink-to-simplify.md)。
- **三条行为判据仍未验证**：宿主是否真的解析 `@docs/teamwork/README.md`、客观产出判据
  是否驱动自发落盘、读取时是否索引先于枚举。本会话内不可验证（子 agent 拿到的是旧
  契约），需在新会话里跑。

## 文档索引

### discussions/

- [Teamwork 收缩为 teamwork-simplify](discussions/teamwork-shrink-to-simplify.md) — Teamwork 相对宿主原生能力的真实增量诊断，收缩为一个 Skill 的方向已定。

### plans/

- [Teamwork 收缩到三样真实增量](plans/teamwork-drop-execution-surface-and-slim-delivery.md) — 执行面还给 harness、交付机器瘦身的范围收缩；已执行并装机，计划里保留启动那一行。
- [Teamwork 契约重设计——补上读取侧，把散文契约换成可执行判据](plans/teamwork-contract-redesign.md) — 读取侧、客观产出判据、kind 判据表已实施并提交；并行/编排部分已被推翻。
- [落盘契约下沉到项目层，并清掉与三样价值无关的脚手架](plans/teamwork-layer-fix-and-cleanup.md) — 分层归位与脚手架清理；两条方向均被推翻，已 superseded。
- [补上 Teamwork 的落盘兜底、配置自检与第五类 guides/](plans/teamwork-persistence-fallback-and-config-doctor.md) — 落盘触发兜底、配置漂移检测、guides/ 落脚点三个结构性缺口；进行中。
- [修掉拆并行线的宿主绑定缺陷，并关闭 1.1.0 验收留下的四条空白](plans/teamwork-split-binding-and-acceptance-gap-closure.md) — 1.1.0 验收留下的四条空白关闭与拆并行线的宿主落点修复；已完成。
- [把三个活跃项目的历史 teamwork 文档迁到当前落盘契约](plans/legacy-teamwork-docs-migration-to-current-contract.md) — 本机三个活跃项目的历史 teamwork 文档迁移到当前契约；已完成。

### records/

- [本机历史 teamwork 文档与当前落盘契约的对齐](records/legacy-teamwork-docs-migration-to-current-contract.md) — 本机 21 个项目历史 teamwork 文档的迁移结果与残留盘点。
- [teamwork-simplify 1.0.0 全功能验收结果](records/teamwork-acceptance-2026-08-29.md) — 安装器、契约层与测试套件的验收结论。

### experiments/、guides/

目前没有文档。
