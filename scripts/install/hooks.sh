# Claude Code SessionStart hook registration.
#
# settings.json is JSON, so it cannot carry the comment markers the policy
# blocks use. The marker here is the hook command's own path: an entry whose
# command names hooks/teamwork-session-check.sh is Teamwork's, and everything
# else in the file — including other SessionStart entries — is the user's and is
# carried through untouched.
TEAMWORK_CLAUDE_HOOK_MARKER="hooks/teamwork-session-check.sh"

teamwork_claude_settings_path() {
  printf '%s\n' "$HOME/.claude/settings.json"
}

teamwork_claude_hook_command() {
  printf '%s\n' "bash $ROOT/hooks/teamwork-session-check.sh"
}

# action is one of: status, install, remove. `status` never writes.
teamwork_claude_hook_apply() {
  local action="$1"
  python3 - "$action" "$(teamwork_claude_settings_path)" "$(teamwork_claude_hook_command)" \
    "$TEAMWORK_CLAUDE_HOOK_MARKER" <<'HOOKPY'
import json
import os
import sys
from pathlib import Path

action, settings_path, command, marker = sys.argv[1:5]
path = Path(settings_path)

if path.is_symlink():
    sys.exit(f"Claude settings is a symlink, not a regular file: {path}")

settings = {}
if path.exists():
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        sys.exit(f"Claude settings is not readable JSON at {path}: {exc}")
    if not isinstance(settings, dict):
        sys.exit(f"Claude settings is not a JSON object at {path}")

hooks = settings.get("hooks")
hooks = hooks if isinstance(hooks, dict) else {}
session_start = hooks.get("SessionStart")
session_start = session_start if isinstance(session_start, list) else []


def is_teamwork(entry):
    if not isinstance(entry, dict):
        return False
    for hook in entry.get("hooks", []) or []:
        if isinstance(hook, dict) and marker in str(hook.get("command", "")):
            return True
    return False


mine = [entry for entry in session_start if is_teamwork(entry)]
theirs = [entry for entry in session_start if not is_teamwork(entry)]

wanted = {
    "hooks": [
        {
            "type": "command",
            "command": command,
            "timeout": 20,
            "statusMessage": "Teamwork doctor",
        }
    ]
}

if action == "status":
    if not mine:
        print("missing")
    elif len(mine) == 1 and mine[0] == wanted:
        print("current")
    else:
        print("stale")
    raise SystemExit(0)

if action == "install":
    session_start = theirs + [wanted]
elif action == "remove":
    if not mine:
        print("absent")
        raise SystemExit(0)
    session_start = theirs
else:
    sys.exit(f"unknown hook action: {action}")

if session_start:
    hooks["SessionStart"] = session_start
else:
    hooks.pop("SessionStart", None)
if hooks:
    settings["hooks"] = hooks
else:
    settings.pop("hooks", None)

path.parent.mkdir(parents=True, exist_ok=True)
temporary = path.with_name(f".{path.name}.teamwork-tmp")
if temporary.exists() or temporary.is_symlink():
    sys.exit(f"temporary path already exists: {temporary}")
try:
    temporary.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if path.exists():
        os.chmod(temporary, path.stat().st_mode)
    else:
        os.chmod(temporary, 0o600)
    os.replace(temporary, path)
finally:
    temporary.unlink(missing_ok=True)
print("installed" if action == "install" else "removed")
HOOKPY
}

install_claude_session_hook() {
  local settings result
  settings="$(teamwork_claude_settings_path)"
  echo "Claude Code user configuration change: registering a SessionStart hook in $settings"
  echo "  command: $(teamwork_claude_hook_command)"
  echo "  effect:  each new session runs ./scripts/doctor.py for that project and prints only errors"
  result="$(teamwork_claude_hook_apply install)"
  if [[ "$(teamwork_claude_hook_apply status)" != "current" ]]; then
    echo "Claude SessionStart hook readback is not current: $settings" >&2
    return 1
  fi
  echo "Claude SessionStart hook: $result (managed readback at $settings)"
  echo "Codex exposes its own hooks file at ~/.codex/hooks.json, but its entry schema is not confirmed here, so nothing is written to it. Cursor has no session-start hook surface on this machine."
}

remove_claude_session_hook() {
  local settings result
  settings="$(teamwork_claude_settings_path)"
  result="$(teamwork_claude_hook_apply remove)"
  if [[ "$(teamwork_claude_hook_apply status)" != "missing" ]]; then
    echo "Claude SessionStart hook is still registered after removal: $settings" >&2
    return 1
  fi
  echo "Claude SessionStart hook: $result ($settings)"
  echo "Nothing else was uninstalled: skills, agents, and the managed policy blocks are untouched."
}

run_doctor() {
  python3 "$ROOT/scripts/doctor.py" "$@"
}
