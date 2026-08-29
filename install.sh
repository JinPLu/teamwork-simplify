#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/install/common.sh
source "$ROOT/scripts/install/common.sh"
# shellcheck source=scripts/install/policy.sh
source "$ROOT/scripts/install/policy.sh"
# shellcheck source=scripts/install/profiles.sh
source "$ROOT/scripts/install/profiles.sh"
# shellcheck source=scripts/install/targets.sh
source "$ROOT/scripts/install/targets.sh"

TARGET=""
PROJECT_ROOT=""
DOCTOR_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)
      INSTALL_MODE="copy"
      shift
      ;;
    --link)
      INSTALL_MODE="link"
      shift
      ;;
    --project-root)
      [[ $# -ge 2 ]] || { echo "--project-root requires a path." >&2; usage; exit 2; }
      if [[ ! -d "$2" ]]; then
        echo "--project-root must be an existing directory: $2" >&2
        usage
        exit 2
      fi
      PROJECT_ROOT="$(cd "$2" 2>/dev/null && pwd)" || {
        echo "--project-root is not an accessible directory: $2" >&2
        usage
        exit 2
      }
      shift 2
      ;;
    --profile)
      [[ $# -ge 2 ]] || { echo "--profile requires a value." >&2; usage; exit 2; }
      CODEX_PROFILE="$2"
      CODEX_PROFILE_SOURCE="cli"
      shift 2
      ;;
    --performance-first)
      CODEX_PROFILE="performance-first"
      CODEX_PROFILE_SOURCE="cli"
      shift
      ;;
    --cost-first)
      CODEX_PROFILE="cost-first"
      CODEX_PROFILE_SOURCE="cli"
      shift
      ;;
    project|project-codex-agents)
      echo "Project-local install targets were removed. Use ./install.sh --project-root <path> init-project to set up only that project's context; refresh global Teamwork surfaces separately." >&2
      usage
      exit 2
      ;;
    doctor)
      if [[ -n "$TARGET" ]]; then
        echo "Specify only one install target." >&2
        usage
        exit 2
      fi
      TARGET="doctor"
      shift
      # doctor owns its own flags (--json, --project PATH); pass them straight
      # through instead of teaching this parser a second flag vocabulary.
      DOCTOR_ARGS=("$@")
      break
      ;;
    codex|cursor|claude|all|update|init-project|codex-agents|cursor-agents|claude-agents|codex-policy|cursor-policy|cursor-policy-copy|claude-policy)
      if [[ -n "$TARGET" ]]; then
        echo "Specify only one install target." >&2
        usage
        exit 2
      fi
      TARGET="$1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

EFFECTIVE_TARGET="${TARGET:-codex}"
if [[ -n "$CODEX_PROFILE_SOURCE" ]] && teamwork_target_uses_codex_profile "$EFFECTIVE_TARGET"; then
  validate_codex_profile
fi

if teamwork_target_is_cursor_only "$EFFECTIVE_TARGET" \
  || teamwork_target_is_claude_only "$EFFECTIVE_TARGET"; then
  if [[ "$CODEX_PROFILE_SOURCE" == "cli" ]]; then
    echo "Profile flags are supported only with Codex targets." >&2
    usage
    exit 2
  fi
fi

if [[ -n "$PROJECT_ROOT" && "$EFFECTIVE_TARGET" != "init-project" ]]; then
  echo "--project-root is valid only with init-project." >&2
  usage
  exit 2
fi

if teamwork_target_uses_codex_profile "$EFFECTIVE_TARGET"; then
  validate_codex_profile
fi

case "$EFFECTIVE_TARGET" in
  codex)
    install_codex
    ;;
  cursor)
    install_cursor
    ;;
  claude)
    install_claude
    ;;
  all)
    install_all
    ;;
  update)
    install_update
    ;;
  init-project)
    init_project
    ;;
  codex-agents)
    install_codex_agents_home
    ;;
  cursor-agents)
    install_cursor_agents_home
    ;;
  claude-agents)
    install_claude_agents_home
    ;;
  codex-policy)
    write_teamwork_codex_global_policy
    ;;
  cursor-policy)
    write_teamwork_cursor_global_policy
    echo "Apply the block above as one Cursor user rule, then confirm it with a rule list readback. A Cursor Agent can do both through Cursor's user-rule API; Settings -> Rules -> User Rules is the manual fallback." >&2
    ;;
  cursor-policy-copy)
    copy_teamwork_cursor_global_policy
    ;;
  claude-policy)
    write_teamwork_claude_global_policy
    ;;
  doctor)
    run_doctor "${DOCTOR_ARGS[@]+"${DOCTOR_ARGS[@]}"}"
    ;;
  *)
    usage
    exit 2
    ;;
esac
