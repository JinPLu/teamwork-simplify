# Contributing

Change the source that owns the behavior:

- `skills/teamwork-collaborate/SKILL.md` owns the collaboration method.
- `policy/teamwork-global.md` owns standing rules and project-context agreements.
- `references/` holds optional examples, not a second rule source.
- Host adapters document installation, permissions and entry points.

Preserve unknown user files in installer changes. Test the real installation,
initialization and diagnostic behavior; do not turn method wording into test
assertions. Public docs explain outcomes and the three layers without copying
the working rules. Local conversation records are not release inputs.

Run `./scripts/validate.sh` for local checks. Use `./scripts/validate.sh --release`
only for explicit release preparation.
