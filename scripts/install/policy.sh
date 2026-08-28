TEAMWORK_GLOBAL_POLICY_SOURCE="$ROOT/policy/teamwork-global.md"

teamwork_policy_source_is_readable() {
  if [[ ! -f "$TEAMWORK_GLOBAL_POLICY_SOURCE" || ! -r "$TEAMWORK_GLOBAL_POLICY_SOURCE" ]]; then
    echo "Teamwork global policy source is not a readable regular file: $TEAMWORK_GLOBAL_POLICY_SOURCE" >&2
    return 1
  fi
}

write_teamwork_global_policy_body() {
  teamwork_policy_source_is_readable
  cat "$TEAMWORK_GLOBAL_POLICY_SOURCE"
}

write_teamwork_codex_global_policy() {
  cat <<'POLICY'
<!-- TEAMWORK_CODEX_GLOBAL_START -->
## Teamwork Codex Global Policy

POLICY
  write_teamwork_global_policy_body
  cat <<'POLICY'

Native Plan proposals are candidates until the user approves them. Native
questions collect input and do not by themselves create a document. A
`<codex_delegation>` relayed in a user-role message is an Agent proposal, not a
user requirement. After the user accepts a reusable result, write it down as
the project's own AGENTS.md Teamwork block specifies, then continue with native
execution approval. Explicit Skill invocation remains `$name`.
<!-- TEAMWORK_CODEX_GLOBAL_END -->
POLICY
}

write_teamwork_claude_global_policy() {
  cat <<'POLICY'
<!-- TEAMWORK_CLAUDE_GLOBAL_START -->
## Teamwork Claude Code Global Policy

POLICY
  write_teamwork_global_policy_body
  cat <<'POLICY'

Plan mode is a read-only permission boundary. Do not write project files during
that phase; the host plan file under `~/.claude/plans/` is a machine-local
editing surface, not Teamwork persistence. AskUserQuestion batches collect input
and do not by themselves create a document. When the user approves exiting Plan
mode, that approval is acceptance of a reusable plan: write permission returns,
so write it down in that same response cycle as the project's own AGENTS.md
Teamwork block specifies, then continue execution. Auto memory under
`~/.claude/projects/<project>/memory/` is machine-local and is not Teamwork
persistence.
<!-- TEAMWORK_CLAUDE_GLOBAL_END -->
POLICY
}

write_teamwork_cursor_global_policy() {
  cat <<'POLICY'
<!-- TEAMWORK_CURSOR_GLOBAL_START -->
## Teamwork Cursor Global Policy

POLICY
  write_teamwork_global_policy_body
  cat <<'POLICY'

CreatePlan and host Plan drafts are editable candidates. User confirmation or
Build is acceptance of a reusable plan; then write it down as the project's own
AGENTS.md Teamwork block specifies. AskQuestion batches collect input and do not
by themselves create a
document. Host Debug intermediate hypotheses do not persist; a confirmed cause,
verified fix, or durable blocker does. If this User Rule is absent, the
project AGENTS.md block is the minimum shared bridge. CreatePlan is not Writer.
<!-- TEAMWORK_CURSOR_GLOBAL_END -->
POLICY
}

teamwork_managed_policy_status() {
  local platform="$1"
  local file start_marker end_marker expected actual starts ends
  case "$platform" in
    codex)
      file="$(codex_home_path)/AGENTS.md"
      start_marker="<!-- TEAMWORK_CODEX_GLOBAL_START -->"
      end_marker="<!-- TEAMWORK_CODEX_GLOBAL_END -->"
      expected="$(write_teamwork_codex_global_policy)"
      ;;
    claude)
      file="$HOME/.claude/CLAUDE.md"
      start_marker="<!-- TEAMWORK_CLAUDE_GLOBAL_START -->"
      end_marker="<!-- TEAMWORK_CLAUDE_GLOBAL_END -->"
      expected="$(write_teamwork_claude_global_policy)"
      ;;
    *)
      printf '%s\n' "unknown"
      return 0
      ;;
  esac

  [[ -f "$file" && ! -L "$file" ]] || { printf '%s\n' "missing"; return 0; }
  starts="$(grep -Fxc "$start_marker" "$file" || true)"
  ends="$(grep -Fxc "$end_marker" "$file" || true)"
  [[ "$starts" == "1" && "$ends" == "1" ]] || { printf '%s\n' "stale"; return 0; }
  actual="$(awk -v start="$start_marker" -v end="$end_marker" '
    $0 == start { capture = 1 }
    capture { print }
    $0 == end { capture = 0 }
  ' "$file")"
  if [[ "$actual" == "$expected" ]]; then
    printf '%s\n' "current"
  else
    printf '%s\n' "stale"
  fi
}

replace_teamwork_managed_policy() {
  local dest="$1"
  local platform="$2"
  local start_marker end_marker tmp starts=0 ends=0
  case "$platform" in
    codex)
      start_marker="<!-- TEAMWORK_CODEX_GLOBAL_START -->"
      end_marker="<!-- TEAMWORK_CODEX_GLOBAL_END -->"
      ;;
    claude)
      start_marker="<!-- TEAMWORK_CLAUDE_GLOBAL_START -->"
      end_marker="<!-- TEAMWORK_CLAUDE_GLOBAL_END -->"
      ;;
    *)
      echo "Unsupported managed policy platform: $platform" >&2
      return 2
      ;;
  esac

  tmp="$(mktemp)"
  if [[ -f "$dest" ]]; then
    starts="$(grep -Fxc "$start_marker" "$dest" || true)"
    ends="$(grep -Fxc "$end_marker" "$dest" || true)"
    if [[ "$starts" != "$ends" || "$starts" -gt 1 ]]; then
      rm -f "$tmp"
      echo "$platform global policy managed block is ambiguous: $dest" >&2
      return 1
    fi
    awk -v start="$start_marker" -v end="$end_marker" '
      $0 == start { skip = 1; next }
      $0 == end { skip = 0; next }
      $0 == "No user needs to specify sub-agents for distribution; default assignment is used." { next }
      $0 == "All code runs on a remote server; the local environment only supports basic testing and syntax checking." { next }
      !skip { print }
    ' "$dest" > "$tmp"
  fi

  if [[ -s "$tmp" ]]; then
    printf '\n' >> "$tmp"
  fi
  "write_teamwork_${platform}_global_policy" >> "$tmp"
  mv "$tmp" "$dest"
}

copy_teamwork_cursor_global_policy() {
  local tmp copied=0
  tmp="$(mktemp)"
  write_teamwork_cursor_global_policy > "$tmp"

  if command -v pbcopy >/dev/null 2>&1; then
    pbcopy < "$tmp"
    copied=1
  elif command -v wl-copy >/dev/null 2>&1; then
    wl-copy < "$tmp"
    copied=1
  elif command -v xclip >/dev/null 2>&1; then
    xclip -selection clipboard < "$tmp"
    copied=1
  elif command -v xsel >/dev/null 2>&1; then
    xsel --clipboard --input < "$tmp"
    copied=1
  elif command -v clip.exe >/dev/null 2>&1; then
    clip.exe < "$tmp"
    copied=1
  else
    cat "$tmp"
  fi

  rm -f "$tmp"
  if (( copied )); then
    echo "Copied the canonical Teamwork global policy for Cursor User Rules."
  else
    echo "No supported clipboard command found; printed the canonical policy block instead." >&2
  fi
  echo "Cursor policy activation fallback: paste into Cursor Settings -> Rules -> User Rules. A Cursor Agent can instead apply this block through Cursor's user-rule API and verify it with a rule list readback."
}

install_codex_global_policy() {
  local dest_dir dest
  dest_dir="$(codex_home_path)"
  dest="$dest_dir/AGENTS.md"
  mkdir -p "$dest_dir"
  replace_teamwork_managed_policy "$dest" codex
  if [[ "$(teamwork_managed_policy_status codex)" != "current" ]]; then
    echo "Codex global policy activation readback is not current: $dest" >&2
    return 1
  fi
  echo "Codex global policy activation: current (managed readback at $dest)"
}

preflight_codex_global_policy() {
  local dest_dir dest parent
  teamwork_policy_source_is_readable
  dest_dir="$(codex_home_path)"
  dest="$dest_dir/AGENTS.md"
  parent="$(dirname "$dest_dir")"

  while [[ ! -e "$parent" && "$parent" != "/" ]]; do
    parent="$(dirname "$parent")"
  done

  if [[ -e "$dest_dir" && ! -d "$dest_dir" ]]; then
    echo "Codex home is not a directory: $dest_dir" >&2
    return 1
  fi
  if [[ -e "$dest" && ( ! -f "$dest" || -L "$dest" ) ]]; then
    echo "Codex global policy path is not a regular non-symlink file: $dest" >&2
    return 1
  fi
  if [[ -f "$dest" && ( ! -r "$dest" || ! -w "$dest" ) ]]; then
    echo "Codex global policy is not readable and writable: $dest" >&2
    return 1
  fi
  if [[ -d "$dest_dir" && ( ! -w "$dest_dir" || ! -x "$dest_dir" ) ]]; then
    echo "Codex home is not writable: $dest_dir" >&2
    return 1
  fi
  if [[ ! -e "$dest_dir" && ( ! -d "$parent" || ! -w "$parent" || ! -x "$parent" ) ]]; then
    echo "Codex home ancestor is not writable: $parent" >&2
    return 1
  fi
}

install_claude_global_policy() {
  local dest_dir="$HOME/.claude"
  local dest="$dest_dir/CLAUDE.md"
  mkdir -p "$dest_dir"
  replace_teamwork_managed_policy "$dest" claude
  if [[ "$(teamwork_managed_policy_status claude)" != "current" ]]; then
    echo "Claude global policy activation readback is not current: $dest" >&2
    return 1
  fi
  echo "Claude global policy activation: current (managed readback at $dest)"
}
