# Contributing

Keep changes small and behavior-led.

- Edit `skills/teamwork-collaborate/SKILL.md` first; it is the sole owner of
  the method.
- Update optional role behavior in `templates/*-agents/`.
- Keep cross-project working rules in `policy/teamwork-global.md` only.
- Preserve unknown user files in installer changes.

Run the fast local smoke:

```bash
./scripts/validate.sh
```

Only explicit release preparation uses:

```bash
./scripts/validate.sh --release
```

Cross-project working rules belong only in `policy/teamwork-global.md`; do
not duplicate them in the Skill body, role templates, tests, or host
adapter docs (`CODEX.md`, `CURSOR.md`, `CLAUDE.md`), which may name host
tools and installer mechanics but not restate a working rule. `README.md`
owns why the standing-policy, on-demand-Skill, and project layers stay
separate, the closed document-kind set, and the path shape; those details
do not belong in the global policy either.
