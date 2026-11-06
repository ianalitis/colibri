#!/usr/bin/env bash
# Fork-only maintenance. Never pushes, switches branches, or merges development work.
set -euo pipefail

action="${1:-status}"
case "$action" in
    status|fetch|sync-main) ;;
    *) echo "Usage: bash scripts/fork-sync.sh [status|fetch|sync-main]" >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo "Expected at most one action" >&2; exit 2; }
cd "$(git rev-parse --show-toplevel)"

if [[ "$action" == sync-main ]]; then
    [[ -z "$(git status --porcelain)" ]] || {
        echo "Refusing sync-main: working tree/index must be clean, including untracked files" >&2
        exit 1
    }
    [[ "$(git symbolic-ref --quiet --short HEAD)" == fork/development ]] || {
        echo "Run sync-main from fork/development; no branches will be switched" >&2
        exit 1
    }
fi

if [[ "$action" != status ]]; then
    git fetch upstream
    git fetch origin
fi
if [[ "$action" == sync-main ]]; then
    # No force refspec: Git refuses a divergent main or one checked out elsewhere.
    git fetch upstream refs/heads/main:refs/heads/main
fi

echo "Cached refs only. Use 'fetch' to refresh. Counts: left-only / right-only."
git status --short --branch
for pair in main...upstream/main origin/main...upstream/main HEAD...upstream/main HEAD...upstream/dev; do
    if git rev-list --left-right --count "$pair" >/dev/null 2>&1; then
        printf '%s\t' "$pair"
        git rev-list --left-right --count "$pair"
    else
        printf '%s\tmissing ref (fetch both remotes)\n' "$pair"
    fi
done
if [[ "$action" == sync-main ]]; then
    echo "Local main synchronized. Development integration and remote publication are separate steps."
fi
