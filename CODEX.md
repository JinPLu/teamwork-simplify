# Codex

Codex is Teamwork's primary runtime. Clone this repository and run:

```bash
./install.sh codex
```

This installs the Skill and the standing policy into `~/.codex/AGENTS.md`
under the `TEAMWORK_CODEX_GLOBAL_START` / `_END` marker. To refresh an
install, run this script again from the checkout you want.

Codex, Cursor, and Claude Code install the same footprint: one Skill and one
managed policy block. Teamwork installs no agents; any this product left on
an earlier release is removed on the next install, and only when the file is
recognized as one it wrote.

Explicit Skill invocation remains
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

## Model tiers

Teamwork installs no agents. A spawned sub-agent inherits the parent model
unless the spawn names its own `model`. Which tier a line gets is the global
policy's delegation rules — weigh cost, speed, and quality by what that line
actually needs. This file
does not pin that to a model name or generation, since Codex's own roster
changes independently of this contract.

## Project setup

Project setup adds or refreshes the project's `AGENTS.md` managed block, a
small `CLAUDE.md` bridge, and `docs/teamwork/README.md` as its reading-side
entry point:

```bash
./install.sh --project-root /absolute/project/path init-project
```

Run the fast local smoke suite with `./scripts/validate.sh`; use
`--release` only during explicit release preparation.
