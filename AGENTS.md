# Teamwork Repository Guidelines

Every component in this repository must pass four checks in order:
1. **Necessary** — drop multi-version shims, redundant wrappers and ceremony that hosts already solve.
2. **Concise** — keep one authoritative source per concern with minimal token and code surface.
3. **Native-first** — leave execution, planning modes, subagents/swarms, tools and permissions to the host.
4. **Human-centered** — optimize for direct causal reasoning, low cognitive load, clear human authority over goals/spend, and zero-noise diagnostics.

## Architecture & Ownership

- `policy/teamwork-global.md` owns standing cross-project preferences (reasoning expression, inline evidence bounds, resource/quota guardrails and zero-ceremony project continuity).
- `skills/teamwork-collaborate/SKILL.md` owns the on-demand collaboration method for weighing competing hypotheses/directions, pre-committing discriminating tests, revising surgically under pushback, maintaining a one-screen decision surface and deriving plans from settled branches. Frontmatter contains only `name` and `description` (`description` starts with `Use when`), with no reference files or rigid document templates. Do not duplicate standing policy rules inside `SKILL.md`.
- `scripts/teamwork.py` (invoked through `./install.sh`) owns host installation (`antigravity`/`agy`, `codex`, `claude`, `cursor`, `all`, `refresh`), `uninstall`, canonical `policy` output, and read-only `doctor` checks. Teamwork installs no agents, hooks or project-local boilerplate blocks.
- `README.md` describes user-visible outcomes and CLI usage concisely without duplicating full policy or skill text.

## Safety & Verification

- Never modify files or user text outside Teamwork's own `teamwork-collaborate` skill entry and `<!-- TEAMWORK_GLOBAL_START --> ... <!-- TEAMWORK_GLOBAL_END -->` managed block. Preflight all target hosts before writing so failed runs make no partial changes.
- Run `./scripts/validate.sh` for behavior tests against throwaway `HOME` directories; use `./scripts/validate.sh --release` when preparing a tagged release on `main`.
