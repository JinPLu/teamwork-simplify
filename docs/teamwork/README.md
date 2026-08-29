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

- 当前活跃方向是
  [Teamwork 契约重设计](plans/teamwork-contract-redesign.md)——常驻契约
  推倒重写，补上此前完全缺失的读取侧、把落盘触发从等待用户接受换成客观
  产出判据、把 kind 判据从优先序改成按问题组织、并新增跨线模型平衡原则；
  这份文件本身就是该计划里"人读文档同步"一步的产出。
- 另外两份计划仍是 active、尚未收口：
  [落盘契约下沉到项目层，并清掉与三样价值无关的脚手架](plans/teamwork-layer-fix-and-cleanup.md)、
  [补上 Teamwork 的落盘兜底、配置自检与第五类 guides/](plans/teamwork-persistence-fallback-and-config-doctor.md)。
- 已收口（status: done）：
  [修掉拆并行线的宿主绑定缺陷，并关闭 1.1.0 验收留下的四条空白](plans/teamwork-split-binding-and-acceptance-gap-closure.md)、
  [把三个活跃项目的历史 teamwork 文档迁到当前落盘契约](plans/legacy-teamwork-docs-migration-to-current-contract.md)。
- 已定方向、不再重开：
  [Teamwork 收缩为 teamwork-simplify](discussions/teamwork-shrink-to-simplify.md)——
  只维护跨宿主常驻规则、讨论到计划的方法、可复用结果落盘三样真实增量，
  宿主原生能力已经覆盖到的面直接删除，不留着跟原生能力并存。

## 文档索引

### discussions/

- [Teamwork 收缩为 teamwork-simplify](discussions/teamwork-shrink-to-simplify.md) — Teamwork 相对宿主原生能力的真实增量诊断，收缩为一个 Skill 的方向已定。

### plans/

- [Teamwork 契约重设计——补上读取侧，把散文契约换成可执行判据](plans/teamwork-contract-redesign.md) — 本次常驻契约重写的计划：读取侧、客观产出判据、kind 判据表、跨线模型平衡；进行中。
- [落盘契约下沉到项目层，并清掉与三样价值无关的脚手架](plans/teamwork-layer-fix-and-cleanup.md) — teamwork-simplify 自身的分层归位与脚手架清理；进行中。
- [补上 Teamwork 的落盘兜底、配置自检与第五类 guides/](plans/teamwork-persistence-fallback-and-config-doctor.md) — 落盘触发兜底、配置漂移检测、guides/ 落脚点三个结构性缺口；进行中。
- [修掉拆并行线的宿主绑定缺陷，并关闭 1.1.0 验收留下的四条空白](plans/teamwork-split-binding-and-acceptance-gap-closure.md) — 1.1.0 验收留下的四条空白关闭与拆并行线的宿主落点修复；已完成。
- [把三个活跃项目的历史 teamwork 文档迁到当前落盘契约](plans/legacy-teamwork-docs-migration-to-current-contract.md) — 本机三个活跃项目的历史 teamwork 文档迁移到当前契约；已完成。

### records/

- [本机历史 teamwork 文档与当前落盘契约的对齐](records/legacy-teamwork-docs-migration-to-current-contract.md) — 本机 21 个项目历史 teamwork 文档的迁移结果与残留盘点。
- [teamwork-simplify 1.0.0 全功能验收结果](records/teamwork-acceptance-2026-08-29.md) — 安装器、契约层与测试套件的验收结论。

### experiments/、guides/

目前没有文档。
