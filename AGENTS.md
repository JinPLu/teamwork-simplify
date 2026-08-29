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
  delegation, and the full project-context contract — both sides of it:
  when to read a project's `docs/teamwork/README.md`, and when a write
  fires, which kind it is, how a subject reuses a path, and the document
  shape. A rule the Skill body already carries does not belong there. Do
  not duplicate a policy rule inside the Skill body, a role template (`templates/*-agents/`),
  a test, or a host adapter doc (`CODEX.md` / `CURSOR.md` / `CLAUDE.md`) —
  those may name host tools and installer mechanics, but the working rule
  itself lives only in `policy/teamwork-global.md`. `README.md` owns the
  three-layer split's rationale; it points at the policy-owned
  project-context contract rather than restating the closed document-kind
  set or the path shape. Commit a change to that file separately from a
  release commit, carrying only the edits needed to keep the tree green.
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
- This project's Teamwork context lives under `docs/teamwork/` at the repository root, with `docs/teamwork/README.md` as the reading-side entry point; the global policy's project-context contract owns it, and this block only adds project-specific detail.
<!-- TEAMWORK_PROJECT_END -->
