# Codex

Codex is Teamwork's primary runtime. Clone this repository and run:

```bash
./install.sh codex
```

This installs the Skill, the three role templates, and the standing policy
into `~/.codex/AGENTS.md` under the `TEAMWORK_CODEX_GLOBAL_START` /
`_END` marker. Run `./install.sh update` to refresh a checkout that is
already installed: it reads `~/.teamwork/install.json`, then replays
`./install.sh <host>` for every host that pointer records — not only
Codex — from the recorded checkout root, regardless of the directory you
run `update` from. A missing, malformed, or no-longer-usable pointer fails
`update` outright; it never falls back to the current directory.

Challenger, Worker, and Writer install as Codex agent profiles under
`~/.codex/agents`. Their availability, installed version, and static routing
state are not preconditions for anything on this host.

Codex, Cursor, and Claude Code install the same footprint: 1 Skill and 3 optional roles. No host omits a role or the Skill.

Root owns integration, user dialogue, and confirmation of what enters the
mainline.
Writer is a dispatch role, not a Skill. Explicit Skill invocation remains
`$teamwork-collaborate`. Native Plan proposals are candidates until the
user approves them; native questions collect input and do not by
themselves create a document. The global policy's project-context
contract — not this file — owns when a write fires, which document kind it
belongs to, and the path it reuses; a project's own `AGENTS.md` Teamwork
block only adds project-specific detail on top (see README.md). Root writes
it, then
continues with native execution approval.

`docs/teamwork/README.md` is the project's own reading side — its current
state on top, a one-line-per-document index below. No Codex-native surface
reads it for you; open it yourself before work that depends on what this
project already decided, concluded, or tried.

Codex role models pin by job under the active `--profile`. With
`performance-first` (the default): Worker uses `gpt-5.6-sol` at medium
effort, Writer uses `gpt-5.6-luna` at high effort, Challenger uses
`gpt-5.6-sol` at high effort. With `--cost-first`, all three pin
`gpt-5.6-luna` at high effort.

Codex's own choice here is coarser than a per-line one: `--profile` sets
one tier for every role for the whole run, not per dispatch. Choosing
`performance-first` against `--cost-first` for a run is still the same
cost/speed/quality trade-off the global policy's delegation rules name for
balancing lines; this file does not pin that choice to a specific model
name or generation, since Codex's own roster changes independently of this
contract.

## Parallel execution surface

`codex --help` (0.147.0) exposes no fan-out subcommand, but the CLI is not
the parallel surface here: in-session `spawn_agent` spawns sub-agents that
run in the same round, alongside `assign_agent_task`, `send_message`,
`wait_agent`, and `close_agent`, bounded by
`max_concurrent_threads_per_session`. Codex's own guidance for that tool is
to look for independent subtasks that can run in parallel within one round.
Independent lines therefore dispatch as several spawns in the same round,
each carried by an installed role profile under `~/.codex/agents`. What this
host lacks is a staged harness that runs rounds for you — staged work is
staged by you, across successive rounds.

Project setup adds or refreshes the project's `AGENTS.md` managed block, a
small `CLAUDE.md` bridge, and `docs/teamwork/README.md` as its reading-side
entry point:

```bash
./install.sh --project-root /absolute/project/path init-project
```

Run the fast local smoke suite with `./scripts/validate.sh`; use
`--release` only during explicit release preparation.
