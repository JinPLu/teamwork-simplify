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

Cross-project working rules — including the full project-context contract
(when to read a project's `docs/teamwork/README.md`, and when a write fires,
which kind it is, how a subject reuses a path, and the document shape) —
belong only in `policy/teamwork-global.md`; do not
duplicate them in the Skill body, role templates, tests, or host adapter
docs (`CODEX.md`, `CURSOR.md`, `CLAUDE.md`), which may name host tools and
installer mechanics but not restate a working rule. `README.md` owns why
the standing-policy, on-demand-Skill, and project layers stay separate; it
points at the policy-owned project-context contract rather than restating
the closed document-kind set or the path shape.
