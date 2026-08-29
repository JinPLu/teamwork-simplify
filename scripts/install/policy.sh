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
user requirement. When the user approves a Plan proposal, that approval makes it
a reusable plan: persist it as the project-context contract above specifies,
then continue with native execution approval. Explicit Skill invocation remains
`$name`.

Independent lines dispatch by spawning the installed role profiles under
`~/.codex/agents` in the same round: that is the default surface here, and it
fits lines that each run one pass and report back once. This host carries no
larger fan-out harness, so work that needs staged rounds is staged by you across
successive rounds — say that is what it will take, and what the extra rounds
cost, before spending it, rather than standing up a substitute harness. Each
installed profile pins its own `model` and `model_reasoning_effort`; the
install-time `--profile` flag chooses which pin set those profiles carry, and a
spawn that names a `model` overrides what it would otherwise inherit.
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
so persist it in that same response cycle as the project-context contract above
specifies, then continue execution. Auto memory under
`~/.claude/projects/<project>/memory/` is machine-local and is not Teamwork
persistence.

Independent lines dispatch as concurrent Task/Agent calls sent in one message:
that is the default surface here, and it fits lines that each run one pass and
report back once. Add `isolation: "worktree"` when two lines write the same
repository, so their edits cannot collide. The Workflow tool is this host's
larger fan-out harness, for work that needs staged rounds rather than one round
of dispatch; it runs only on the user's explicit opt-in, so propose it with the
reason and the cost it carries and let the user decide — never enable it on your
own judgement. An agent type's model, reasoning effort, and tools come from its
definition in `~/.claude/agents/<role>.md` frontmatter (`model`, `effort`); the
`model` parameter on a dispatch overrides that definition for that one call.
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
Build is acceptance of a reusable plan; then persist it as the project-context
contract above specifies. AskQuestion batches collect input and do not
by themselves create a
document. Host Debug intermediate hypotheses do not persist; a confirmed cause,
verified fix, or durable blocker does. If this User Rule is absent, the
project AGENTS.md block is the minimum shared bridge. CreatePlan is not Writer.

Independent lines dispatch through the installed role agents under
`~/.cursor/agents`, one dispatch per line: that is the default surface here, and
it fits lines that each run one pass and report back once. Give a line its own
worktree when two lines write the same repository. This host carries no fan-out
harness, and its cloud-worker and background surfaces spend the user's own
environment and account, so work that needs staged rounds is staged by you
across successive rounds; propose the larger surface with the reason and the
cost and let the user decide, rather than starting one on your own judgement.
Each installed role agent pins its own `model` and carries reasoning effort
inside that same value as `<model>[effort=...]`; the same bracketed form given
at invocation time overrides that pin.
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
    # Only the managed block is touched. Everything outside the markers is the
    # user's own file: it is carried through unchanged, except for trailing
    # blank lines, which are dropped so the separator below stays idempotent.
    awk -v start="$start_marker" -v end="$end_marker" '
      $0 == start { skip = 1; next }
      $0 == end { skip = 0; next }
      skip { next }
      { kept[++count] = $0 }
      END {
        while (count > 0 && kept[count] ~ /^[[:space:]]*$/) { count-- }
        for (index_ = 1; index_ <= count; index_++) { print kept[index_] }
      }
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
