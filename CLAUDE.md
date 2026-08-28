@AGENTS.md

# Claude Code adapter

Claude Code reads `CLAUDE.md`, not `AGENTS.md`; the import line above is what
lets this file pull in the repository's own working conventions.

```bash
./install.sh claude
```

This installs the Skill and the three role templates, and writes the
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
  as the global policy's Teamwork bridge specifies in the same response
  cycle, then continue.
- **Explore** handles live local search directly; do not name a custom
  agent `Explore` — that identifier overrides the built-in.
- **`code-review`** is the host's own independent-review surface; Teamwork
  installs no Reviewer role.
- **Auto memory** under `~/.claude/projects/<project>/memory/` is
  machine-local and is not Teamwork persistence.

`AskUserQuestion` batches collect input and do not by themselves create a
document. After the user accepts a reusable result, the global policy's
Teamwork bridge owns when that write fires, which of the four document
kinds it belongs to, and the path it reuses (see README.md); a project's
own `AGENTS.md` Teamwork block only adds project-specific detail on top.
Root writes it in the same response cycle.

## Parallel execution surface

When the split verdict says two or more lines are independent, Claude Code
offers two surfaces, in this order:

- **Concurrent `Task`/`Agent` dispatch** — several agent calls sent in one
  message run at the same time. Always available, no opt-in. Pass
  `isolation: "worktree"` when two lines write to the same repository, so
  their edits cannot collide.
- **The `Workflow` tool** — the host's own fan-out harness, which a user
  typically asks for as a dynamic workflow. It runs only on the user's
  explicit opt-in (their own words, the `ultracode` keyword, or a Skill that
  calls it) and can spawn many agents, so Root proposes it and names the
  cost; Root never enables it on its own judgement.

Worker is the fallback for a host with neither, not the first choice here.

## Roles and models

`Task`/`Agent` dispatches the three optional roles: Challenger, Worker, and
Writer. Writer is a dispatch role, not a Skill. Claude agents pin models by
job and ignore `--profile` (that flag applies to Codex agents only):
Challenger runs Opus at xhigh effort, Worker runs Sonnet at high effort,
and Writer runs Sonnet at medium effort. `CLAUDE_CODE_SUBAGENT_MODEL` and a
per-dispatch model both override the pin; an unpinned role inherits the
session model and effort.

A Cursor install that refreshes this Claude skill root still installs the
full Claude set. When both `~/.cursor/skills/` and `~/.claude/skills/` hold
the same Teamwork copy, which one a dual-host session reads is not
guaranteed — keep both in sync via the installers.
