# Teamwork

<p align="center">
  <a href="README.md">中文</a> ·
  <a href="CODEX.md">Codex</a> ·
  <a href="docs/architecture.md">Architecture</a>
</p>

---

Teamwork is a thin layer on top of Codex, Cursor, and Claude Code. It does
not duplicate what the host already does natively — Plan, question flows,
Debug, code review. It adds only two things the hosts do not provide on
their own: one standing set of working rules that holds in every project,
and one method that carries "discuss the direction, settle a plan, split
it into parallel work" all the way through.

## What it solves

Clear, authorized work should run directly, with no workflow gate in front
of it. What is actually missing is a different thing: when the direction
is not settled yet and several parallel lines need to turn a fuzzy goal
into an executable plan together, native Plan mode usually only writes the
plan — it does not carry "discuss the options, confirm the direction,
split the independent work, hand it to bounded Workers, then integrate and
verify the results" as one connected path. Teamwork installs exactly that
one method, three optional roles to carry out the split work, and four
document kinds to remember the parts of that path worth reusing across
sessions.

## Start in one minute

```bash
git clone <this-repository-url>
cd teamwork-simplify
./install.sh claude   # or codex / cursor-policy
```

- `./install.sh codex` installs the Skill, the three role templates, and
  the standing policy into Codex (the policy is written to
  `~/.codex/AGENTS.md`).
- `./install.sh claude` installs the same set into Claude Code (the policy
  is written to `~/.claude/CLAUDE.md`).
- `./install.sh cursor` installs the Skill and roles; `./install.sh
  cursor-policy` separately prints (and tries to copy) the standing policy
  text, because Cursor's User Rules live in its own settings store, not a
  file the installer can write directly — this step needs a manual paste
  into Settings -> Rules -> User Rules.

## What the one Skill does

Teamwork ships exactly one public Skill: `teamwork-collaborate`. It carries
work that genuinely needs a shared direction from discussion through to a
verified result:

1. **Discuss**: lay out the options and trade-offs that actually matter;
   no question asked just to fill a process step.
2. **Direction**: converge on a direction you accept and have confirmed.
3. **Executable plan**: turn the direction into ordered, verifiable steps
   with stop conditions.
4. **Split parallel lines**: separate the independent steps into lines
   that can move at the same time.
5. **Dispatch Workers**: hand each line's bounded task to a Worker.
6. **Integrate and verify**: collect the results, check the real evidence,
   and decide whether to merge them or return to discussion.

Name it with `$teamwork-collaborate` in Codex, or `/teamwork-collaborate`
in Cursor and Claude Code. Work whose outcome and boundaries are already
clear does not need it — just ask for the result directly.

## Three optional roles

The Skill's split work is carried out by three bounded, optional roles.
None of them blocks the main path when missing:

| Role | What it does |
| --- | --- |
| Challenger | Finds real counter-evidence and overlooked costs in an already-formed direction or plan; it does not propose new options. |
| Worker | Completes one parallel line's bounded task inside a given write scope and returns the result with evidence. |
| Writer | Turns a result the method owner has already certified into readable Markdown under `docs/teamwork/<kind>/`, without changing facts or conclusions; if it cannot write, it returns `no-write` and the exact gap, and Root reports the path that was not delivered. |

Root delegates only when parallel investigation, independent judgment, or
a clean division of work is actually useful. A handoff carries only five
fields: objective, owned scope, settled constraints, available evidence,
requested return.

## Four readable document types

<!-- BEGIN GENERATED: persistence-en -->
When a native interaction or `teamwork-collaborate` reaches a reusable semantic result and you accept that result, Root writes plain Markdown under `docs/teamwork/<kind>/` in the same response cycle. Entering a host surface is not itself a write, and you do not need to name the Skill first. Writer helps only when that does not delay the write. Each document carries both a **current synthesis** and an append-only **chronological history**, so it is quick to read without hiding how the conclusion changed. Default paths are `docs/teamwork/<kind>/<slug>.md`; reuse the path for the same stable identity.

| Document | What it records |
| --- | --- |
| 💬 Discussion | Options, trade-offs, settled choices, rejected alternatives, and open questions. |
| 📝 Plan | Executable steps, dependencies, parallel lines and Worker dispatch, verification, and stop conditions for a selected direction. |
| 📌 Record | Reusable results, conclusions, and blockers that carry across sessions. |
| 🧪 Experiment | One trial's claim, setup, actual run, result, and conclusion. |
<!-- END GENERATED: persistence-en -->

Documents require no Case, schema, JSON index, or migration state, and no
document is needed when nothing reusable changed. See
[`docs/teamwork/README.md`](docs/teamwork/README.md) for details.

## Project setup

To add only lightweight Teamwork guidance to one project, with no database
or runtime state created:

```bash
./install.sh --project-root /absolute/project/path init-project
```

This only adds or refreshes one `AGENTS.md` managed block (Claude Code
reads `CLAUDE.md`, not `AGENTS.md`, so it also adds a one-line `@AGENTS.md`
import).

## Learn more

- [Architecture](docs/architecture.md): why the standing policy layer and
  the on-demand Skill layer must stay physically separate, plus source
  ownership, the Agent handoff, and the closed set of four document kinds.
- [Codex](CODEX.md) / [Cursor](CURSOR.md) / [Claude Code](CLAUDE.md): install
  steps and the native-capability mapping for each host.
- [Contributing](CONTRIBUTING.md): canonical owners and verification
  commands.
- [`docs/teamwork/README.md`](docs/teamwork/README.md): what each document
  kind maintains, the granularity for opening one, and frontmatter
  conventions.

License: [MIT](LICENSE)
