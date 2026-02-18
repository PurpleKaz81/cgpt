#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/gh_retry.sh <command> [args...]

Environment variables:
  GH_RETRY_ATTEMPTS       Total attempts (default: 5)
  GH_RETRY_INITIAL_DELAY  Initial delay in seconds (default: 2)
  GH_RETRY_MAX_DELAY      Max delay in seconds (default: 30)
  GH_RETRY_BACKOFF        Backoff multiplier (default: 2)

Example:
  scripts/gh_retry.sh gh api rate_limit
EOF
}

is_integer() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

is_transient_error() {
  local text="$1"
  if [[ "$text" =~ error\ connecting\ to\ api\.github\.com ]]; then
    return 0
  fi
  if [[ "$text" =~ (TLS\ handshake\ timeout|i/o\ timeout|timed\ out|connection\ reset\ by\ peer|temporarily\ unavailable|EOF) ]]; then
    return 0
  fi
  if [[ "$text" =~ (502|503|504) ]]; then
    return 0
  fi
  if [[ "$text" =~ (Secondary\ rate\ limit|secondary\ rate\ limit|rate\ limit\ exceeded) ]]; then
    return 0
  fi
  return 1
}

if (( $# == 0 )); then
  usage >&2
  exit 2
fi

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

attempts="${GH_RETRY_ATTEMPTS:-5}"
initial_delay="${GH_RETRY_INITIAL_DELAY:-2}"
max_delay="${GH_RETRY_MAX_DELAY:-30}"
backoff="${GH_RETRY_BACKOFF:-2}"

for value in "$attempts" "$initial_delay" "$max_delay" "$backoff"; do
  if ! is_integer "$value"; then
    echo "gh-retry: retry settings must be positive integers" >&2
    exit 2
  fi
done

if (( attempts < 1 || initial_delay < 1 || max_delay < 1 || backoff < 1 )); then
  echo "gh-retry: retry settings must be >= 1" >&2
  exit 2
fi

delay="$initial_delay"
attempt=1

while true; do
  stdout_capture="$(mktemp)"
  stderr_capture="$(mktemp)"
  set +e
  "$@" >"$stdout_capture" 2>"$stderr_capture"
  status=$?
  set -e

  cat "$stdout_capture"
  cat "$stderr_capture" >&2

  if (( status == 0 )); then
    rm -f "$stdout_capture"
    rm -f "$stderr_capture"
    exit 0
  fi

  err_text="$(cat "$stderr_capture")"
  rm -f "$stdout_capture"
  rm -f "$stderr_capture"

  if ! is_transient_error "$err_text"; then
    exit "$status"
  fi

  if (( attempt >= attempts )); then
    echo "gh-retry: giving up after ${attempt} attempt(s)" >&2
    exit "$status"
  fi

  echo "gh-retry: transient failure (attempt ${attempt}/${attempts}), retrying in ${delay}s..." >&2
  sleep "$delay"

  next_delay=$(( delay * backoff ))
  if (( next_delay > max_delay )); then
    delay="$max_delay"
  else
    delay="$next_delay"
  fi
  attempt=$(( attempt + 1 ))
done
