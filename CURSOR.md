# Cursor

```bash
./install.sh cursor
./install.sh cursor-policy
```

The Skill is copied to `~/.cursor/skills/`; invoke `/teamwork-collaborate`.
Paste the printed policy block into Settings → Rules → User Rules, replacing
its previous Teamwork block. `cursor-policy-copy` copies the block without
printing it. The installer cannot read Cursor's settings store to verify activation.

A Cursor install also refreshes an existing Teamwork-managed Claude Skill root,
because dual-host discovery can otherwise leave different copies available.
Codex or Claude installs do not refresh Cursor's Skill root.

For project setup, run:

```bash
./install.sh --project-root /absolute/project/path init-project
```

The managed AGENTS.md block declares the project entry. Native Cursor modes,
permissions and tools govern execution. Working agreements live in
[the shared policy](policy/teamwork-global.md); [README](README.md) explains
scope and [CONTRIBUTING](CONTRIBUTING.md) lists validation commands.
