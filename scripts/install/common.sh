INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
CODEX_PROFILE="${TEAMWORK_CODEX_PROFILE:-performance-first}"
CODEX_PROFILE_SOURCE=""
if [[ -n "${TEAMWORK_CODEX_PROFILE:-}" ]]; then
  CODEX_PROFILE_SOURCE="env"
fi
CURSOR_SKILL_PROFILE_TOKEN="inherit"
CLAUDE_SKILL_PROFILE_TOKEN="inherit"
CODEX_USER_SKILLS_ROOT="$HOME/.agents/skills"
PKG_VERSION="unknown"
if [[ -f "$ROOT/VERSION" ]]; then
  PKG_VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
fi
SKILLS=(teamwork-collaborate)
CURSOR_SKILLS=(teamwork-collaborate)
CLAUDE_SKILLS=(teamwork-collaborate)
CODEX_SKILLS=(teamwork-collaborate)
RETIRED_SKILLS=(
  grill-me
  teamwork-design
  teamwork-discuss
  using-teamwork
  teamwork-execute
  teamwork
  teamwork-plan
  teamwork-review
  teamwork-research
  teamwork-debug
  teamwork-goal
  teamwork-init
  teamwork-update
)
LEGACY_CODEX_ROUTER_SKILL="teamwork"
CLAUDE_AGENTS=(challenger worker writer)
CURSOR_AGENTS=(challenger worker writer)
CODEX_AGENTS=(teamwork-challenger teamwork-worker teamwork-writer)
RETIRED_CLAUDE_AGENTS=(designer plan-reviewer explorer researcher planner reviewer debugger)
RETIRED_CURSOR_AGENTS=(designer plan-reviewer explorer debugger researcher planner reviewer)
RETIRED_CODEX_AGENTS=(teamwork-designer teamwork-plan-reviewer teamwork-researcher teamwork-planner teamwork-reviewer teamwork-debugger teamwork-explorer)

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh [--copy|--link] \
    cursor|cursor-agents|cursor-policy|cursor-policy-copy

  ./install.sh [--copy|--link] \
    claude|claude-agents|claude-policy

  ./install.sh [--copy|--link] [--profile performance-first|cost-first] \
    [--project-root PATH] \
    codex|all|update|init-project|codex-agents|codex-policy

Targets:
  codex          Install Codex skills/agents from this checkout and separately
                 activate the managed Codex global policy
                 (script default target)
  cursor         Compatibility/development target: install skills/agents and
                 report the separate manual Cursor User Rules activation action
  claude         Compatibility/development target: install skills/agents and
                 separately activate the managed Claude global policy
  all            Compatibility/development target: install static surfaces for
                 all hosts, activate observable Codex/Claude policy, and
                 report Cursor policy as partial
  update         Refresh Teamwork's Codex global surfaces from this checkout
  init-project   Add or refresh one concise Teamwork block in a project's
                 AGENTS.md, plus the small CLAUDE.md import that lets a host
                 which reads CLAUDE.md load it, without changing global
                 settings
  codex-agents   Install Teamwork Codex custom agents to ~/.codex/agents
  cursor-agents  Compatibility/development: install Teamwork Cursor subagents
                 to ~/.cursor/agents
  claude-agents  Compatibility/development: install Teamwork Claude subagents
                 to ~/.claude/agents
  codex-policy   Print the canonical policy in its Codex managed wrapper
  cursor-policy  Compatibility/development: print the Teamwork Cursor global
                 policy block for one Cursor user rule
  cursor-policy-copy
                 Compatibility/development: copy that block to the clipboard
                 for the manual Settings -> Rules paste fallback
  claude-policy  Compatibility/development: print the canonical policy in its
                 Claude managed wrapper

Default mode is --copy. Clone this repository and run ./install.sh <host>.
Official support and release qualification are Codex-only. Use --link for local
development when installs should track this checkout.
`--project-root` is valid with `init-project`.

Teamwork never installs, configures, or checks external MCP servers or compute
tools. Install and configure optional tools through their own documentation.

Profile flags apply to Codex targets only.
Cursor and Claude Code targets reject --profile, --performance-first, and
--cost-first.
Profile defaults to performance-first for Codex; choose cost-first explicitly
when needed.
On Codex, performance-first uses Sol/high for Challenger, Sol/medium for
Worker, and Luna/high for Writer.
On Codex, cost-first uses Luna/high for Challenger, Worker, and Writer.
Claude Code agents pick models by job and ignore --profile: Challenger pins
Opus at xhigh; Worker pins Sonnet at high; Writer pins Sonnet at medium.
Claude Code skill-root ownership writes `.teamwork-profile` with the
host-neutral token `inherit`.
Cursor agents pick models by job: Challenger and Worker pin Grok 4.6 Fast at
high effort; Writer pins Grok 4.6 Fast at medium effort. `--profile` still
does not apply to Cursor. Cursor skill-root ownership still writes
`.teamwork-profile` with the host-neutral token `inherit`.
USAGE
}


teamwork_target_is_cursor_only() {
  case "${1:-}" in
    cursor|cursor-agents|cursor-policy|cursor-policy-copy)
      return 0
      ;;
  esac
  return 1
}

teamwork_target_is_claude_only() {
  case "${1:-}" in
    claude|claude-agents|claude-policy)
      return 0
      ;;
  esac
  return 1
}

teamwork_target_uses_codex_profile() {
  case "${1:-}" in
    codex|all|update|codex-agents)
      return 0
      ;;
  esac
  return 1
}

validate_codex_profile() {
  case "$CODEX_PROFILE" in
    performance-first|cost-first)
      ;;
    *)
      echo "Unknown profile: $CODEX_PROFILE" >&2
      usage
      exit 2
      ;;
  esac
}


preflight_agent_destination() {
  local root="$1"
  local extension="$2"
  local label="$3"
  shift 3
  local agent path
  if [[ -e "$root" && ! -d "$root" ]]; then
    echo "$label agent path is not a directory: $root" >&2
    return 1
  fi
  if [[ -d "$root" && ( ! -w "$root" || ! -x "$root" ) ]]; then
    echo "$label agent path is not writable: $root" >&2
    return 1
  fi
  for agent in "$@"; do
    path="$root/$agent.$extension"
    if [[ -e "$path" || -L "$path" ]]; then
      if [[ ! -f "$path" || ! -w "$path" ]]; then
        echo "$label agent is not a writable regular file: $path" >&2
        return 1
      fi
      if ! teamwork_markdown_agent_file_is_recognized "$path" "$agent"; then
        echo "$label agent $path is not a recognized Teamwork-owned profile; refusing to replace it." >&2
        return 1
      fi
    fi
  done
}


teamwork_skill_entry_has_known_inventory() {
  local root="$1"
  local skill="$2"
  local entry="$root/$skill"
  local path relative

  if retired_skill_is_configured "$skill"; then
    teamwork_retired_skill_entry_is_owned "$root" "$skill"
    return
  fi
  if [[ -L "$entry" ]]; then
    teamwork_skill_entry_is_named "$root" "$skill"
    return
  fi
  [[ -d "$entry" ]] || return 1
  [[ ! -e "$entry/SKILL.md" ]] || teamwork_skill_entry_is_named "$root" "$skill" || return 1
  while IFS= read -r -d '' path; do
    relative="${path#"$entry"/}"
    [[ ! -L "$path" ]] || return 1
    [[ -e "$ROOT/skills/$skill/$relative" ]] \
      || teamwork_retired_reference_is_configured "$skill" "$relative" \
      || return 1
  done < <(find "$entry" -mindepth 1 -print0)
}


teamwork_retired_reference_is_configured() {
  local skill="$1"
  local relative="$2"
  case "$skill/$relative" in
    teamwork-collaborate/references|teamwork-collaborate/references/adversarial-search.md|\
    teamwork-collaborate/references/experiment.md|teamwork-collaborate/agents|\
    teamwork-collaborate/agents/openai.yaml|\
    teamwork-debug/references|teamwork-debug/references/runtime-diagnosis.md|\
    teamwork-research/references|teamwork-research/references/deep-research.md|\
    teamwork-review/references|teamwork-review/references/strict-review.md)
      return 0
      ;;
  esac
  return 1
}


retired_skill_is_configured() {
  local skill="$1"
  local retired
  for retired in "${RETIRED_SKILLS[@]}"; do
    [[ "$skill" == "$retired" ]] && return 0
  done
  return 1
}


teamwork_skill_root_has_markers() {
  local root="$1"
  [[ -f "$root/.teamwork-version" && -f "$root/.teamwork-profile" ]]
}

teamwork_retired_skill_entry_is_owned() {
  local root="$1"
  local retired="$2"
  local entry="$root/$retired"
  local skill_file="$entry/SKILL.md"

  if [[ "$retired" == "$LEGACY_CODEX_ROUTER_SKILL" ]]; then
    teamwork_skill_root_has_markers "$root"
    return
  fi
  teamwork_skill_root_has_markers "$root" && return 0
  [[ -f "$skill_file" ]] || return 1
  grep -q "^name: $retired$" "$skill_file" && grep -qi "teamwork" "$skill_file"
}

remove_retired_skill() {
  local dest_root="$1"
  local retired="$2"
  local dest="$dest_root/$retired"
  local link="$dest/SKILL.md"
  local raw_target resolved

  if teamwork_skill_root_has_markers "$dest_root"; then
    rm -rf "$dest"
    return 0
  fi

  if [[ -L "$dest" ]]; then
    raw_target="$(readlink "$dest" 2>/dev/null || true)"
    resolved="$(readlink -f "$dest" 2>/dev/null || true)"
    if [[ "$raw_target" == */skills/"$retired" || "$resolved" == */skills/"$retired" ]]; then
      rm -f "$dest"
    fi
    return 0
  fi

  [[ -e "$link" || -L "$link" ]] || return 0

  if [[ -L "$link" ]]; then
    raw_target="$(readlink "$link" 2>/dev/null || true)"
    resolved="$(readlink -f "$link" 2>/dev/null || true)"
    if [[ "$raw_target" == */skills/"$retired"/SKILL.md || "$resolved" == */skills/"$retired"/SKILL.md ]]; then
      rm -f "$link"
      rmdir "$dest" 2>/dev/null || true
    fi
    return 0
  fi

  [[ -f "$link" ]] || return 0
  grep -q "^name: $retired$" "$link" || return 0
  if teamwork_retired_skill_entry_is_owned "$dest_root" "$retired"; then
    rm -rf "$dest"
  else
    echo "Preserved unrecognized retired Skill: $dest" >&2
  fi
}

install_skill_dir() {
  local source="$1"
  local dest="$2"

  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  case "$INSTALL_MODE" in
    copy)
      cp -R "$source" "$dest"
      ;;
    link)
      ln -sfn "$source" "$dest"
      ;;
    *)
      echo "Unknown install mode: $INSTALL_MODE" >&2
      usage
      exit 2
      ;;
  esac
}

install_agent_file() {
  local source="$1"
  local dest="$2"

  rm -f "$dest"
  mkdir -p "$(dirname "$dest")"
  case "$INSTALL_MODE" in
    copy)
      cp "$source" "$dest"
      ;;
    link)
      ln -sfn "$source" "$dest"
      ;;
    *)
      echo "Unknown install mode: $INSTALL_MODE" >&2
      usage
      exit 2
      ;;
  esac
}


install_skill_set() {
  local dest_root="$1"
  local label="$2"
  local profile_token="${3:-$CODEX_PROFILE}"
  local host="${4:-}"
  local skill retired

  preflight_teamwork_skill_root "$dest_root" "$label skill root"
  mkdir -p "$dest_root"
  for retired in "${RETIRED_SKILLS[@]}"; do
    remove_retired_skill "$dest_root" "$retired"
  done

  case "$host" in
    cursor)
      for skill in "${CURSOR_SKILLS[@]}"; do
        install_skill_dir "$ROOT/skills/$skill" "$dest_root/$skill"
      done
      ;;
    claude)
      for skill in "${CLAUDE_SKILLS[@]}"; do
        install_skill_dir "$ROOT/skills/$skill" "$dest_root/$skill"
      done
      ;;
    codex)
      for skill in "${CODEX_SKILLS[@]}"; do
        install_skill_dir "$ROOT/skills/$skill" "$dest_root/$skill"
      done
      ;;
    "")
      for skill in "${SKILLS[@]}"; do
        install_skill_dir "$ROOT/skills/$skill" "$dest_root/$skill"
      done
      ;;
    *)
      echo "Unknown skill-set host: $host" >&2
      return 1
      ;;
  esac

  printf '%s\n' "$PKG_VERSION" > "$dest_root/.teamwork-version"
  printf '%s\n' "$profile_token" > "$dest_root/.teamwork-profile"

  echo "Installed $label skills under: $dest_root ($INSTALL_MODE)"
}

codex_home_path() {
  printf '%s\n' "${CODEX_HOME:-$HOME/.codex}"
}

legacy_plugin_activation_path() {
  printf '%s/teamwork/plugin-activation.json\n' "$(codex_home_path)"
}

legacy_plugin_activation_is_present() {
  local path
  path="$(legacy_plugin_activation_path)"
  [[ -e "$path" || -L "$path" ]]
}

remove_legacy_plugin_activation() {
  local path
  path="$(legacy_plugin_activation_path)"
  if [[ -L "$path" || -f "$path" ]]; then
    rm -f "$path"
    echo "Removed leftover Teamwork Codex plugin activation marker: $path"
    return 0
  fi
  if [[ -e "$path" ]]; then
    echo "Leftover plugin activation path is not a regular file: $path" >&2
    return 1
  fi
}

write_source_pointer() {
  local path
  path="$(
    python3 "$ROOT/scripts/write-source-pointer.py" write \
      --root "$ROOT" \
      --version "$PKG_VERSION" \
      --home "$HOME" \
      "$@"
  )"
  echo "Recorded Teamwork source pointer: $path"
}

teamwork_skill_entry_is_named() {
  local root="$1"
  local skill="$2"
  local entry="$root/$skill"
  local skill_file="$entry/SKILL.md"
  [[ -f "$skill_file" ]] || return 1
  grep -q "^name: $skill$" "$skill_file"
}

teamwork_skill_entry_identity_is_safe() {
  local root="$1"
  local skill="$2"
  local entry="$root/$skill"
  local skill_file="$entry/SKILL.md"

  if [[ -L "$entry" ]]; then
    teamwork_skill_entry_is_named "$root" "$skill"
    return
  fi
  [[ -d "$entry" ]] || return 1
  [[ ! -e "$skill_file" ]] || teamwork_skill_entry_is_named "$root" "$skill"
}

preflight_teamwork_skill_root() {
  local root="$1"
  local label="$2"
  local skip_legacy_router="${3:-0}"
  local marker="$root/.teamwork-version"
  local profile_marker="$root/.teamwork-profile"
  local skill found=0

  for skill in "${SKILLS[@]}" "${RETIRED_SKILLS[@]}"; do
    if [[ "$skip_legacy_router" == "1" && "$skill" == "$LEGACY_CODEX_ROUTER_SKILL" ]]; then
      continue
    fi
    if [[ -e "$root/$skill" || -L "$root/$skill" ]]; then
      found=1
      if retired_skill_is_configured "$skill"; then
        if teamwork_retired_skill_entry_is_owned "$root" "$skill"; then
          if [[ -d "$root/$skill" && ! -L "$root/$skill" && ! -w "$root/$skill" ]]; then
            echo "$label contains a non-writable retired Teamwork Skill: $skill" >&2
            return 1
          fi
        fi
        continue
      fi
      if [[ ! -f "$marker" || ! -f "$profile_marker" ]]; then
        echo "$label contains $skill without Teamwork ownership markers; refusing to replace it." >&2
        return 1
      fi
      if ! teamwork_skill_entry_identity_is_safe "$root" "$skill"; then
        echo "$label contains an unrecognized $skill entry; refusing to replace it." >&2
        return 1
      fi
      if ! teamwork_skill_entry_has_known_inventory "$root" "$skill"; then
        echo "$label contains an unrecognized $skill entry; refusing to replace it." >&2
        return 1
      fi
    fi
  done

  if (( found == 0 )) && [[ -e "$marker" || -e "$profile_marker" ]]; then
    if [[ ! -f "$marker" || ! -f "$profile_marker" ]]; then
      echo "$label has incomplete Teamwork ownership markers; refusing to modify it." >&2
      return 1
    fi
  fi
}

preflight_legacy_codex_skills() {
  local legacy_root="$1"
  preflight_teamwork_skill_root "$legacy_root" "Legacy Codex skills" 1
}

legacy_codex_router_copy_is_owned() {
  local legacy_root="$1"
  local entry="$legacy_root/$LEGACY_CODEX_ROUTER_SKILL"

  [[ -e "$entry" || -L "$entry" ]] || return 0
  [[ -d "$entry" && ! -L "$entry" ]] || return 1
  # `teamwork` is a generic name. Never claim it from prose or frontmatter
  # alone; only root-level Teamwork ownership markers authorize cleanup.
  teamwork_skill_root_has_markers "$legacy_root"
}

preflight_owned_legacy_cleanup() {
  local legacy_root="$1"
  local skill entry dir
  local found=0

  [[ -d "$legacy_root" ]] || return 0
  for skill in "${SKILLS[@]}" "${RETIRED_SKILLS[@]}" "$LEGACY_CODEX_ROUTER_SKILL"; do
    entry="$legacy_root/$skill"
    if [[ "$skill" == "$LEGACY_CODEX_ROUTER_SKILL" ]] \
      && ! legacy_codex_router_copy_is_owned "$legacy_root"; then
      continue
    fi
    if [[ -e "$entry" || -L "$entry" ]]; then
      found=1
      if [[ -d "$entry" && ! -L "$entry" ]]; then
        while IFS= read -r -d '' dir; do
          if [[ ! -w "$dir" || ! -x "$dir" ]]; then
            echo "Legacy Codex skill cleanup is not writable at $dir; refusing migration before installing the new root." >&2
            return 1
          fi
        done < <(find "$entry" -type d -print0)
      fi
    fi
  done

  if (( found == 1 )) || [[ -e "$legacy_root/.teamwork-version" || -e "$legacy_root/.teamwork-profile" ]]; then
    if [[ ! -w "$legacy_root" || ! -x "$legacy_root" ]]; then
      echo "Legacy Codex skill cleanup is not writable at $legacy_root; refusing migration before installing the new root." >&2
      return 1
    fi
  fi
}

remove_owned_legacy_codex_skills() {
  local legacy_root="$1"
  local skill retired
  [[ -d "$legacy_root" ]] || return 0

  for skill in "${SKILLS[@]}"; do
    if [[ -e "$legacy_root/$skill" || -L "$legacy_root/$skill" ]] \
        && teamwork_skill_entry_has_known_inventory "$legacy_root" "$skill"; then
      rm -rf "$legacy_root/$skill"
    fi
  done
  for retired in "${RETIRED_SKILLS[@]}"; do
    remove_retired_skill "$legacy_root" "$retired"
  done
  rm -f "$legacy_root/.teamwork-version" "$legacy_root/.teamwork-profile"
  rmdir "$legacy_root" 2>/dev/null || true
}

remove_legacy_codex_router_copy() {
  local legacy_root="$1"
  local entry="$legacy_root/$LEGACY_CODEX_ROUTER_SKILL"

  [[ -e "$entry" || -L "$entry" ]] || return 0
  legacy_codex_router_copy_is_owned "$legacy_root" || return 0
  rm -rf "$entry"
  rmdir "$legacy_root" 2>/dev/null || true
}

install_codex_skill_set() {
  local dest_root="$CODEX_USER_SKILLS_ROOT"
  local legacy_root="$(codex_home_path)/skills"

  preflight_teamwork_skill_root "$dest_root" "Codex user skill root"
  if [[ "$legacy_root" != "$dest_root" ]]; then
    preflight_legacy_codex_skills "$legacy_root"
    preflight_owned_legacy_cleanup "$legacy_root"
  fi
  install_skill_set "$dest_root" "Codex" "$CODEX_PROFILE" "codex"
  if [[ "$legacy_root" != "$dest_root" ]]; then
    remove_owned_legacy_codex_skills "$legacy_root"
    remove_legacy_codex_router_copy "$legacy_root"
  fi
}
