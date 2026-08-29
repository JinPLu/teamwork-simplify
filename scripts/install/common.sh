INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
# Written next to .teamwork-version inside an installed skill root. The pair is
# what marks that root as this product's; the token itself carries no meaning
# any more, and the ownership guard only checks that both files exist.
SKILL_ROOT_MARKER_TOKEN="inherit"
CODEX_USER_SKILLS_ROOT="$HOME/.agents/skills"
PKG_VERSION="unknown"
if [[ -f "$ROOT/VERSION" ]]; then
  PKG_VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
fi
SKILLS=(teamwork-collaborate)
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
# Teamwork installs no agents. Every name below was installed by an earlier
# release and is removed on the next install, but only from a file this product
# is recognized to have written — see teamwork_*_agent_file_is_recognized.
RETIRED_CLAUDE_AGENTS=(challenger worker writer designer plan-reviewer explorer researcher planner reviewer debugger)
RETIRED_CURSOR_AGENTS=(challenger worker writer designer plan-reviewer explorer debugger researcher planner reviewer)
RETIRED_CODEX_AGENTS=(teamwork-challenger teamwork-worker teamwork-writer teamwork-designer teamwork-plan-reviewer teamwork-researcher teamwork-planner teamwork-reviewer teamwork-debugger teamwork-explorer)

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh [--copy|--link] codex|cursor|claude|all
  ./install.sh [--copy|--link] codex-policy|cursor-policy|cursor-policy-copy|claude-policy
  ./install.sh --project-root PATH init-project
  ./install.sh doctor [--project PATH] [--json]

Targets:
  codex          Install the Skill from this checkout and activate the managed
                 Codex global policy (script default target)
  cursor         Install the Skill and report the separate manual Cursor User
                 Rules activation action
  claude         Install the Skill and activate the managed Claude global policy
  all            Install for all three hosts
  init-project   Add or refresh one project's Teamwork block in AGENTS.md, the
                 small CLAUDE.md bridge, and docs/teamwork/README.md, without
                 changing global settings
  codex-policy   Print the canonical policy in its Codex managed wrapper
  cursor-policy  Print the Teamwork Cursor global policy block for one user rule
  cursor-policy-copy
                 Copy that block to the clipboard for the manual
                 Settings -> Rules paste
  claude-policy  Print the canonical policy in its Claude managed wrapper
  doctor         Read-only health check of the installed surfaces and of every
                 project on this machine that carries a Teamwork block or a
                 docs/teamwork/ tree; writes nothing, exits non-zero on an error

Default mode is --copy; use --link for local development when installs should
track this checkout. To refresh an install, run this script again from the
checkout you want.

Teamwork installs no agents and no hooks. Agents an earlier release installed
are removed on the next install, and only when the file is recognized as one
this product wrote.

Teamwork never installs, configures, or checks external MCP servers or compute
tools. Install and configure optional tools through their own documentation.
USAGE
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

# A symlink is Teamwork-owned evidence only when it points back at a checkout's
# `skills/<suffix>` path. `suffix` is `<retired>` for a linked Skill directory
# and `<retired>/SKILL.md` for a linked Skill file.
teamwork_retired_skill_link_is_owned() {
  local link="$1"
  local suffix="$2"
  local raw_target resolved

  [[ -L "$link" ]] || return 1
  raw_target="$(readlink "$link" 2>/dev/null || true)"
  resolved="$(readlink -f "$link" 2>/dev/null || true)"
  [[ "$raw_target" == */skills/"$suffix" || "$resolved" == */skills/"$suffix" ]]
}

# Root-level ownership markers say the root was installed into; they say nothing
# about who owns one entry inside it. Ownership of a retired entry is decided by
# that entry's own signature: a Teamwork SKILL.md, or a symlink into a checkout.
teamwork_retired_skill_entry_is_owned() {
  local root="$1"
  local retired="$2"
  local entry="$root/$retired"
  local skill_file="$entry/SKILL.md"

  if [[ -L "$entry" ]]; then
    teamwork_retired_skill_link_is_owned "$entry" "$retired"
    return
  fi
  [[ -d "$entry" ]] || return 1
  if [[ -L "$skill_file" ]]; then
    teamwork_retired_skill_link_is_owned "$skill_file" "$retired/SKILL.md"
    return
  fi
  [[ -f "$skill_file" ]] || return 1
  grep -q "^name: $retired$" "$skill_file" || return 1
  # A retired `teamwork*` name puts the word "teamwork" in its own frontmatter
  # name line, so that line proves nothing. Ownership needs a Teamwork mention
  # somewhere else in the file.
  grep -vi "^name:" "$skill_file" | grep -qi "teamwork" || return 1
  # `teamwork` is the most generic name of all: require root-level ownership
  # markers on top of the signature before claiming it.
  if [[ "$retired" == "$LEGACY_CODEX_ROUTER_SKILL" ]]; then
    teamwork_skill_root_has_markers "$root" || return 1
  fi
  return 0
}

remove_retired_skill() {
  local dest_root="$1"
  local retired="$2"
  local dest="$dest_root/$retired"

  [[ -e "$dest" || -L "$dest" ]] || return 0

  if ! teamwork_retired_skill_entry_is_owned "$dest_root" "$retired"; then
    echo "Preserved unrecognized retired Skill: $dest" >&2
    return 0
  fi

  if [[ -L "$dest" ]]; then
    rm -f "$dest"
  elif [[ -L "$dest/SKILL.md" ]]; then
    rm -f "$dest/SKILL.md"
    rmdir "$dest" 2>/dev/null || true
  else
    rm -rf "$dest"
  fi
  echo "Removed retired Teamwork Skill: $dest"
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
  local skill retired

  preflight_teamwork_skill_root "$dest_root" "$label skill root"
  mkdir -p "$dest_root"
  for retired in "${RETIRED_SKILLS[@]}"; do
    remove_retired_skill "$dest_root" "$retired"
  done
  for skill in "${SKILLS[@]}"; do
    install_skill_dir "$ROOT/skills/$skill" "$dest_root/$skill"
  done

  printf '%s\n' "$PKG_VERSION" > "$dest_root/.teamwork-version"
  printf '%s\n' "$SKILL_ROOT_MARKER_TOKEN" > "$dest_root/.teamwork-profile"

  echo "Installed $label skills under: $dest_root ($INSTALL_MODE)"
}

# An agent file is this product's only when its own content says so. Name
# matching is not enough: a user may keep an agent whose name resembles a
# retired Teamwork one, and that file must survive untouched.
teamwork_codex_agent_file_is_recognized() {
  local path="$1"
  local agent="$2"
  local expected_name
  expected_name="${agent//-/_}"
  [[ -f "$path" ]] \
    && grep -q "^name = \"$expected_name\"$" "$path" \
    && grep -Eq 'You are (the )?Teamwork ' "$path"
}

teamwork_markdown_agent_file_is_recognized() {
  local path="$1"
  local agent="$2"
  [[ -f "$path" ]] \
    && grep -Fqx "name: $agent" "$path" \
    && grep -Eq '^You are (the )?Teamwork ' "$path"
}

remove_retired_agent_files() {
  local platform="$1"
  local root="$2"
  shift 2
  local agent extension path

  case "$platform" in
    codex) extension=toml ;;
    cursor|claude) extension=md ;;
    *) return 1 ;;
  esac

  [[ -d "$root" ]] || return 0
  for agent in "$@"; do
    path="$root/$agent.$extension"
    [[ -e "$path" || -L "$path" ]] || continue
    if [[ "$platform" == "codex" ]] && teamwork_codex_agent_file_is_recognized "$path" "$agent"; then
      rm -f "$path"
      echo "Removed retired Teamwork agent: $path"
    elif [[ "$platform" != "codex" ]] && teamwork_markdown_agent_file_is_recognized "$path" "$agent"; then
      rm -f "$path"
      echo "Removed retired Teamwork agent: $path"
    else
      echo "Preserved unrecognized retired agent file: $path" >&2
    fi
  done
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
  # alone, and never from root-level markers alone: the entry must carry the
  # Teamwork SKILL.md signature *and* sit under a Teamwork-owned root.
  teamwork_retired_skill_entry_is_owned "$legacy_root" "$LEGACY_CODEX_ROUTER_SKILL"
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
  install_skill_set "$dest_root" "Codex"
  if [[ "$legacy_root" != "$dest_root" ]]; then
    remove_owned_legacy_codex_skills "$legacy_root"
    remove_legacy_codex_router_copy "$legacy_root"
  fi
}
