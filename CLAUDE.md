@AGENTS.md

# Claude Code adapter

Claude Code reads `CLAUDE.md`, not `AGENTS.md`; the import line above is what
lets this file pull in the repository's own working conventions.

```bash
./install.sh claude
```

This installs the Skill and writes the
standing policy into `~/.claude/CLAUDE.md` under the
`TEAMWORK_CLAUDE_GLOBAL_START` / `_END` marker. Invoke the Skill with
`/teamwork-collaborate`; Codex uses `$teamwork-collaborate` instead.

## Native capability mapping

Claude Code already has Plan mode, built-in Explore, and `code-review`.
Teamwork does not add a second implementation of any of them:

- **Plan mode** is a read-only permission boundary, not Teamwork
  persistence. Writing project files during Plan mode is not itself a
  write; the host plan file under `~/.claude/plans/` is a machine-local
  editing surface. When the user approves exiting Plan mode, that approval
  is acceptance of a reusable plan — write permission returns, so persist it
  as the global policy's project-context contract specifies in the same
  response cycle, then continue.
- **Explore** handles live local search directly; do not name a custom
  agent `Explore` — that identifier overrides the built-in.
- **`code-review`** is the host's own independent-review surface; Teamwork
  installs no Reviewer role.
- **Auto memory** under `~/.claude/projects/<project>/memory/` is
  machine-local and is not Teamwork persistence; it does not substitute for
  reading `docs/teamwork/README.md`, the project-local reading side, before
  work that depends on this project's prior decisions.

`AskUserQuestion` batches collect input and do not by themselves create a
document. The global policy's project-context contract — not this file —
owns when a write fires, which document kind it belongs to, and the path it
reuses
(see README.md); a project's own `AGENTS.md` Teamwork block only adds
project-specific detail on top. Root writes it in the same response
cycle.

## Model tiers

Teamwork installs no agents. A dispatch names its own `model` and `effort`
and inherits the session's when it names neither. Which tier a line gets is
the global policy's delegation rules — weigh cost, speed, and quality by what
that line actually needs. This file does not pin that to a model name or
generation, since Claude Code's own roster changes independently of this
contract.

A Cursor install that refreshes this Claude skill root still installs the
full Claude set. When both `~/.cursor/skills/` and `~/.claude/skills/` hold
the same Teamwork copy, which one a dual-host session reads is not
guaranteed — keep both in sync via the installers.

<!-- TEAMWORK_CLAUDE_BRIDGE_START -->
<!-- The project's Teamwork reading-side entry point, loaded into every session's context. -->
@docs/teamwork/README.md
<!-- TEAMWORK_CLAUDE_BRIDGE_END -->
