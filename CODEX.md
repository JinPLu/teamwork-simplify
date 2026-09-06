# Codex

```bash
./install.sh codex
./install.sh --project-root /absolute/project/path init-project
```

The installer copies the Skill to `~/.agents/skills/` and updates only its
managed block in `$CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`).
Run the same command from the desired checkout to refresh it; `--link` is
available for local development.

Invoke the Skill with `$teamwork-collaborate`. Codex loads AGENTS.md as project
instructions. Its native modes, tools and permissions govern execution.
The project entry location is declared in the managed project block.

Use `./install.sh doctor --project /absolute/project/path` to inspect the local
installation and project links. Working agreements live in
[the shared policy](policy/teamwork-global.md); see [README](README.md) for
product scope and [CONTRIBUTING](CONTRIBUTING.md) for validation commands.
