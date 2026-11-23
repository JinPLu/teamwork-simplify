# Teamwork Repository Guidelines

Every component in this repository must pass four checks in order:
1. **Necessary** — drop multi-version shims, redundant wrappers and ceremony that hosts already solve.
2. **Concise** — keep one authoritative source per concern with minimal token and code surface.
3. **Native-first** — leave execution, planning modes, subagents/swarms, tools and permissions to the host.
4. **Human-centered** — optimize for direct judgment, low cognitive load, clear human authority over goals/spend, and zero-noise diagnostics.

## Architecture & Rule Ownership

Apply a strict placement test before adding or moving any rule:
- **`policy/teamwork-global.md`** owns *only* standing cross-project preferences and cross-host living-memory invariants that must stay active before any Skill loads and after context compaction. Keep it free of prose formulas, syntactic code ban lists and document templates.
- **`skills/teamwork-collaborate/SKILL.md`** owns *only* on-demand multi-turn collaboration moves (ground verification, staged global-to-local decisions, pre-committed discriminating tests, surgical revision under pushback, living topic decision view and settled-branch plan handoff). Frontmatter contains only `name` and `description` (`description` starts with `Use when `), with zero `references/` files and zero duplication of `policy/teamwork-global.md`.
- **`README.md`** stays concise and outcome-focused (purpose, 4-check philosophy, 2-file boundary, CLI usage and 4-host table) without multi-version history or paraphrasing policy/skill prose.
- **`scripts/teamwork.py`** (invoked via `./install.sh`) owns the 4-host CLI (`antigravity`/`agy`, `codex`, `claude`, `cursor`, `all`, `refresh`, `uninstall`, `policy`) and read-only `doctor` (global hosts + current directory when `docs/teamwork/` exists, or opt-in `--project PATH`), with zero multi-version marker shims. Teamwork installs no agents, hooks or project-local boilerplate blocks.

## Safety & Verification

- Never modify files or user text outside Teamwork's own `teamwork-collaborate` Skill entry and `<!-- TEAMWORK_GLOBAL_START --> ... <!-- TEAMWORK_GLOBAL_END -->` managed block. Preflight all target hosts before writing so failed runs make no partial changes.
- Run `./scripts/validate.sh` to verify shell syntax, semver `VERSION`, `SKILL.md` single-file/frontmatter invariants, and throwaway-`HOME` behavior tests.
