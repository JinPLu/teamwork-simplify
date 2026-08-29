preflight_claude_global_policy() {
  local dest_dir="$HOME/.claude"
  local dest="$dest_dir/CLAUDE.md"
  local parent
  parent="$(dirname "$dest_dir")"

  while [[ ! -e "$parent" && "$parent" != "/" ]]; do
    parent="$(dirname "$parent")"
  done

  if [[ -e "$dest_dir" && ! -d "$dest_dir" ]]; then
    echo "Claude home is not a directory: $dest_dir" >&2
    return 1
  fi
  if [[ -e "$dest" && ! -f "$dest" ]]; then
    echo "Claude global policy path is not a regular file: $dest" >&2
    return 1
  fi
  if [[ -f "$dest" && ( ! -r "$dest" || ! -w "$dest" ) ]]; then
    echo "Claude global policy is not readable and writable: $dest" >&2
    return 1
  fi
  if [[ -d "$dest_dir" && ( ! -w "$dest_dir" || ! -x "$dest_dir" ) ]]; then
    echo "Claude home is not writable: $dest_dir" >&2
    return 1
  fi
  if [[ ! -e "$dest_dir" && ( ! -d "$parent" || ! -w "$parent" || ! -x "$parent" ) ]]; then
    echo "Claude home ancestor is not writable: $parent" >&2
    return 1
  fi
}

install_codex() {
  remove_legacy_plugin_activation
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Codex user skill root"
  preflight_legacy_codex_skills "$(codex_home_path)/skills"
  preflight_owned_legacy_cleanup "$(codex_home_path)/skills"
  preflight_codex_global_policy
  install_codex_skill_set
  remove_retired_agent_files codex "$(codex_home_path)/agents" "${RETIRED_CODEX_AGENTS[@]}"
  echo "Codex Skill: installed"
  install_codex_global_policy
}

install_cursor() {
  local skill_root="$HOME/.cursor/skills"
  local claude_skill_root="$HOME/.claude/skills"
  preflight_teamwork_skill_root "$skill_root" "Cursor skill root"
  install_skill_set "$skill_root" "Cursor"
  remove_retired_agent_files cursor "$HOME/.cursor/agents" "${RETIRED_CURSOR_AGENTS[@]}"
  echo "Cursor Skill: installed"
  if teamwork_skill_root_has_markers "$claude_skill_root"; then
    install_skill_set "$claude_skill_root" "Claude Code"
    echo "Both Teamwork skill roots were refreshed; when both exist, which copy wins is not guaranteed."
  fi
  echo "Cursor global policy activation: separate; this installer cannot reach Cursor's user-rule store."
  echo "Exact action: run ./install.sh cursor-policy, then have a Cursor Agent add or update that block as one user rule and confirm it with a rule list readback."
}

install_claude() {
  local skill_root="$HOME/.claude/skills"
  preflight_teamwork_skill_root "$skill_root" "Claude Code skill root"
  preflight_claude_global_policy
  install_skill_set "$skill_root" "Claude Code"
  remove_retired_agent_files claude "$HOME/.claude/agents" "${RETIRED_CLAUDE_AGENTS[@]}"
  echo "Claude Skill: installed"
  install_claude_global_policy
}

install_all() {
  remove_legacy_plugin_activation
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Codex user skill root"
  preflight_legacy_codex_skills "$(codex_home_path)/skills"
  preflight_owned_legacy_cleanup "$(codex_home_path)/skills"
  preflight_teamwork_skill_root "$HOME/.cursor/skills" "Cursor skill root"
  preflight_teamwork_skill_root "$HOME/.claude/skills" "Claude Code skill root"
  preflight_codex_global_policy
  preflight_claude_global_policy
  install_codex_skill_set
  remove_retired_agent_files codex "$(codex_home_path)/agents" "${RETIRED_CODEX_AGENTS[@]}"
  echo "Codex Skill: installed"
  install_codex_global_policy
  install_skill_set "$HOME/.cursor/skills" "Cursor"
  remove_retired_agent_files cursor "$HOME/.cursor/agents" "${RETIRED_CURSOR_AGENTS[@]}"
  echo "Cursor Skill: installed"
  echo "Cursor global policy activation: separate; this installer cannot reach Cursor's user-rule store."
  echo "Exact action: run ./install.sh cursor-policy, then have a Cursor Agent add or update that block as one user rule and confirm it with a rule list readback."
  install_skill_set "$HOME/.claude/skills" "Claude Code"
  remove_retired_agent_files claude "$HOME/.claude/agents" "${RETIRED_CLAUDE_AGENTS[@]}"
  echo "Claude Skill: installed"
  install_claude_global_policy
}

run_doctor() {
  python3 "$ROOT/scripts/doctor.py" "$@"
}

init_project() {
  local base="${PROJECT_ROOT:-$PWD}"
  "$ROOT/scripts/init-project.sh" --project-root "$base"
}
