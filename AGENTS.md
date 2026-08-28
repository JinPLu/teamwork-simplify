# teamwork-simplify Repository

`skills/` is the source of truth: there is exactly one Skill,
`teamwork-collaborate`, and its `SKILL.md` owns the method. Clear,
authorized work stays native; the Skill adds only the method described by
its own trigger. Cursor and Claude Code adapters are optional compatibility
surfaces and never block Codex work.

## Working Conventions

- Change `skills/teamwork-collaborate/SKILL.md` before workflow behavior.
  Public docs stay outcome-focused; they do not restate the method.
- `policy/teamwork-global.md` exclusively owns cross-project working rules
  that must hold before the Skill loads, plus the minimum routing,
  delegation, and persistence bridge. A rule the Skill body already carries
  does not belong there. Do not duplicate a policy rule inside the Skill
  body, a role template (`templates/*-agents/`), a test, or a host adapter
  doc (`CODEX.md` / `CURSOR.md` / `CLAUDE.md`) — those may name host tools
  and installer mechanics, but the working rule itself lives only in
  `policy/teamwork-global.md`. `README.md` owns the two-layer split's
  rationale, the closed document-kind set, and the path shape; those
  details do not belong in the global policy either. Commit a change to
  that file separately from a release commit, carrying only the edits
  needed to keep the tree green.
- Shell scripts use Bash with `set -euo pipefail`, quoted variables, and
  arrays. `skills/teamwork-collaborate/SKILL.md` frontmatter has only `name`
  and `description`, and `description` starts with `Use when`.
- Agent delegation to Challenger, Worker, or Writer is optional unless the
  user explicitly requires independent work. A handoff carries only
  objective, scope, settled constraints, evidence, and requested return.
  A missing role never triggers Update automatically.
- Project-local Teamwork setup is one concise managed `AGENTS.md` block plus
  a small `CLAUDE.md` import. It has no document database, schema, case
  lifecycle, or migration gate.

## Commands

- Run `./scripts/validate.sh` for the small local smoke suite. Use
  `./scripts/validate.sh --release` only for explicit release preparation.
- `init-project` maintains the project instruction block;
  `./install.sh update` refreshes an existing checkout's installed surfaces.

## Releases

- Release on `main` unless the user explicitly requests another Git
  workflow.
- VERSION consistency is checked by `./scripts/validate.sh`.
- A release is complete only after the requested verification, commit, tag,
  and any requested GitHub Release succeed. Cursor/Claude adapters and
  project-local files are not release blockers.
- Keep release notes short and describe user-visible behavior rather than
  internal tests, gates, or version history.

<!-- TEAMWORK_PROJECT_START -->
## Teamwork Project Instructions

- Project label: `teamwork-simplify`.
- Teamwork adds no required project-local workflow or state. It creates no empty directory, schema, or mandatory stage chain. Native host modes stay in charge. Follow this project's normal instructions and invoke a named Skill only when its trigger matches.
- When the user accepts a reusable semantic result, write it to `docs/teamwork/<kind>/<slug>.md` in the same response cycle, whether or not a Skill was named. Chat, host plans, and todos are not cross-session memory. An ordinary next action is not a checkpoint.
- The kind set is closed. Write `discussions/` when a decision, recommendation, or unresolved-question batch will change later work; its identity is the final goal plus the subject. Write `plans/` when the direction and scope, the first executable plan, or a material replan is accepted; its identity is the selected outcome. Write `records/` when a result, conclusion, or blocker can be reused by a later session; its identity is the continuing objective. Write `experiments/` when one trial has a result or a conclusion; its identity is that experiment.
- The same identity reuses the same path. Each document keeps the current synthesis at the top and an append-only dated History at the bottom; a correction is a new entry, never a rewrite. Keep the user's original wording separate from your working understanding.
<!-- TEAMWORK_PROJECT_END -->
