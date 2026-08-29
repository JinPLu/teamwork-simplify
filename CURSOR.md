# Cursor adapter

```bash
./install.sh cursor
./install.sh cursor-policy
```

`cursor` installs the Skill and the three role templates under
`~/.cursor/skills/`. Invoke the Skill with `/teamwork-collaborate`; Codex
uses `$teamwork-collaborate` instead. Policy activation is a separate step
because Cursor keeps User Rules in its own settings store, not a file the
installer owns: `./install.sh cursor-policy` prints the standing policy
block (and tries to copy it to the clipboard) for a manual paste into
Settings -> Rules -> User Rules; `./install.sh cursor-policy-copy` copies it
without printing the confirmation instructions. The
`TEAMWORK_CURSOR_GLOBAL_START` marker in that block is what keeps a repeat
paste an update instead of a duplicate.

Privacy Mode (Legacy) blocks Cursor's User Rule API, so the policy paste is
not a usable path in that mode. The Skill is self-sufficient without it;
the project `AGENTS.md` managed block is the minimum shared bridge. This is
the one layer of Teamwork that can silently go stale — nothing detects a
User Rule that was never pasted or that drifted from a later policy
change, because the installer cannot read Cursor's User Rules back.

When both `~/.cursor/skills/` and `~/.claude/skills/` hold the same
Teamwork copy, which one Cursor reads is not guaranteed — keep both in
sync. `./install.sh cursor` refreshes the Claude skill root when that copy
is already present.

## Native capability mapping

Cursor already has Plan, Debug, Explore, and `AskQuestion`. Teamwork does
not add a second implementation of any of them:

- **CreatePlan** and host Plan drafts are editable candidates; user
  confirmation or Build is acceptance of a reusable plan, then the Skill's
  persistence contract applies. CreatePlan is not Writer.
- **Debug** intermediate hypotheses do not persist; a confirmed cause,
  verified fix, or durable blocker does, through the Skill's own
  persistence contract when that work was reached through
  `teamwork-collaborate`.
- **Explore** and **AskQuestion** handle live search and batched questions
  directly; a question batch collects input and does not by itself create
  a document. Neither reads `docs/teamwork/README.md` for you — open it
  yourself before work that depends on what this project already decided,
  concluded, or tried.
- `.cursor/plans` remains the host editing surface. The global policy's
  project-context contract owns when a write fires, which document kind it
  belongs to, and the path it reuses (see README.md); a project's own
  `AGENTS.md` Teamwork block only adds project-specific detail on top. Root
  writes it
  there. If the User Rule above is absent, the project `AGENTS.md` block is
  still the minimum shared bridge.

## Parallel execution surface

`cursor-agent --help` exposes no fan-out subcommand. An independent line is
carried by dispatching the installed role agents under `~/.cursor/agents`,
one per line, so Worker is the primary vehicle here rather than a fallback.
`-w, --worktree [name]` starts a line in an isolated git worktree under
`~/.cursor/worktrees/`, which is how two lines writing the same repository
stay off each other. The `worker` subcommand starts a private cloud worker
that spends the user's own environment and account, so it is proposed with
its cost, never started on the agent's own judgement.

## Roles and models

Cursor roles pin `model` by job; `--profile` does not apply to Cursor and
the Cursor install does not rewrite these pins. Challenger and Worker pin
Grok 4.6 Fast at high effort; Writer pins Grok 4.6 Fast at medium effort.

Cursor's own choice here is coarser than a per-dispatch one: each role
pins one fixed model, and a dispatch does not vary it per line. The
global policy's delegation rules still name the underlying cost/speed/
quality trade-off for balancing lines; on this host that surfaces as how
many Worker lines to run rather than varying any single line's tier. This
file does not pin that trade-off to a specific model name or generation,
since Cursor's own roster changes independently of this contract.
