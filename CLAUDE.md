@AGENTS.md

# Claude Code

```bash
./install.sh claude
./install.sh --project-root /absolute/project/path init-project
```

The installer copies the Skill to `~/.claude/skills/` and updates its managed
policy block in `~/.claude/CLAUDE.md`. Refresh by rerunning the install from the
checkout you want; `--link` is available for development.

Invoke `/teamwork-collaborate`. Claude Code uses CLAUDE.md for project
instructions; the import above shares this repository's AGENTS.md.
Plan mode restricts project-file writes. Project initialization manages this
bridge separately from user-authored content.

Use `./install.sh doctor --project /absolute/project/path` for diagnostics.
Working agreements live in [the shared policy](policy/teamwork-global.md).

<!-- TEAMWORK_CLAUDE_BRIDGE_START -->
<!-- TEAMWORK_CLAUDE_BRIDGE_END -->
