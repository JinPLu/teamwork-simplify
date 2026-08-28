# Contributing

Keep changes small and behavior-led.

- Edit `skills/teamwork-collaborate/SKILL.md` first; it is the sole owner of
  the method.
- Update optional role behavior in `templates/*-agents/`.
- Keep cross-project working rules in `policy/teamwork-global.md` only.
- Repeated public facts (document kinds, host counts, path shapes) live in
  `config/teamwork-facts.yaml`; after changing them, run
  `python3 scripts/render-teamwork-facts.py`.
- The Skill/role inventory lives in `config/teamwork-topology.json`; the
  installer reads it through `scripts/teamwork_tooling/topology.py`.
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
tools and installer mechanics but not restate a working rule.
`docs/architecture.md` owns the closed document-kind set, the path shape,
and why the standing-policy and on-demand-Skill layers stay separate; those
details do not belong in the global policy either.
