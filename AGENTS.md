# teamwork-simplify Repository

`skills/` is the source of truth: there is exactly one Skill,
`teamwork-collaborate`, and its `SKILL.md` owns the method. Clear,
authorized work stays native; the Skill adds only the method described by
its own trigger. Cursor and Claude Code adapters are optional compatibility
surfaces and never block Codex work.

## Working Conventions

- Change `skills/teamwork-collaborate/SKILL.md` before workflow behavior.
  Public docs stay outcome-focused; they do not restate the method.
- `policy/teamwork-global.md` exclusively owns standing cross-project rules,
  minimal native routing and the complete, concise project-context agreement.
  The Skill owns the discussion and planning method; examples are optional.
  Do not duplicate standing rules in the Skill, tests or host adapter docs.
  Adapters describe installation, permissions and entry points. `README.md`
  explains the three layers through user-visible outcomes. Keep policy edits
  separate from a release commit when a release is requested.
- The Code section's prohibition list in `policy/teamwork-global.md` is a
  frequency-ordered cache of observed agent failures, not a taxonomy. A new
  item enters only from a failure actually observed in this or another
  project; an item that stops recurring comes out. Keep it short enough that
  every entry still competes for attention.
- Shell scripts use Bash with `set -euo pipefail`, quoted variables, and
  arrays. `skills/teamwork-collaborate/SKILL.md` frontmatter has only `name`
  and `description`, and `description` starts with `Use when`.
- Teamwork installs no agents and no hooks, and adds no orchestration of its
  own. Execution runs on the host's own subagent and fan-out surfaces; the
  method delivers the requested assessment, decision or plan.
- Project-local Teamwork setup is one concise managed `AGENTS.md` block plus
  a small `CLAUDE.md` import. It has no document database, schema, case
  lifecycle, or migration gate.

## Commands

- Run `./scripts/validate.sh` for the small local smoke suite. Use
  `./scripts/validate.sh --release` only for explicit release preparation.
- `init-project` maintains the project instruction block;
  To refresh an install, run `./install.sh <host>` again from the checkout
  you want.

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
- Shared working agreements come from the installed Teamwork global policy; this block adds only project-specific context.
- Project context entry: `docs/teamwork/README.md` at this repository root.
<!-- TEAMWORK_PROJECT_END -->
