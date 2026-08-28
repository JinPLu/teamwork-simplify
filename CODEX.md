# Codex

Codex is Teamwork's primary runtime. Clone this repository and run:

```bash
./install.sh codex
```

This installs the Skill, the three role templates, and the standing policy
into `~/.codex/AGENTS.md` under the `TEAMWORK_CODEX_GLOBAL_START` /
`_END` marker. Run `./install.sh update` to refresh a checkout that is
already installed; `~/.teamwork/install.json` records which checkout
`update` reads from.

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
the project's own `AGENTS.md` Teamwork block — not this file — owns when
that write fires, which of the four document kinds it belongs to, and the
path it reuses (see README.md's persistence sections); Root writes it,
then continues with native execution approval.

Codex role models pin by job under the active `--profile`. With
`performance-first` (the default): Worker uses `gpt-5.6-sol` at medium
effort, Writer uses `gpt-5.6-luna` at high effort, Challenger uses
`gpt-5.6-sol` at high effort. With `--cost-first`, all three pin
`gpt-5.6-luna` at high effort.

Project setup adds only one managed block to `AGENTS.md`:

```bash
./install.sh --project-root /absolute/project/path init-project
```

Run the fast local smoke suite with `./scripts/validate.sh`; use
`--release` only during explicit release preparation.
