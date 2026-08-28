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
themselves create a document. After the user accepts a reusable result,
the global policy's Teamwork bridge — not this file — owns when that write
fires, which of the four document kinds it belongs to, and the path it
reuses; a project's own `AGENTS.md` Teamwork block only adds
project-specific detail on top (see README.md). Root writes it, then
continues with native execution approval.

Codex role models pin by job under the active `--profile`. With
`performance-first` (the default): Worker uses `gpt-5.6-sol` at medium
effort, Writer uses `gpt-5.6-luna` at high effort, Challenger uses
`gpt-5.6-sol` at high effort. With `--cost-first`, all three pin
`gpt-5.6-luna` at high effort.

## Parallel execution surface

`codex --help` (0.147.0) exposes no native fan-out subcommand — no workflow
loop, no parallel-agent harness. On this host an independent line is carried
by the installed Worker profile under `~/.codex/agents`, one dispatch per
line, which makes Worker the primary vehicle here rather than a fallback.

Project setup adds only one managed block to `AGENTS.md`:

```bash
./install.sh --project-root /absolute/project/path init-project
```

Run the fast local smoke suite with `./scripts/validate.sh`; use
`--release` only during explicit release preparation.
