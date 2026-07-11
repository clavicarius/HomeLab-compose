#!/usr/bin/env bash
# Loads GIT_AUTHOR_* and GIT_COMMITTER_* from .git-author into the current shell.
# Usage: source ./scripts/git-author-env.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUTHOR_FILE="${ROOT}/.git-author"

if [ ! -f "${AUTHOR_FILE}" ]; then
    echo "Error: ${AUTHOR_FILE} not found." >&2
    echo "Copy .git-author.example to .git-author and set your name and email." >&2
    return 1 2>/dev/null || exit 1
fi

set -a
# shellcheck disable=SC1090
. "${AUTHOR_FILE}"
set +a

export GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-${GIT_AUTHOR_NAME:-}}"
export GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-${GIT_AUTHOR_EMAIL:-}}"

if [ -z "${GIT_AUTHOR_NAME:-}" ] || [ -z "${GIT_AUTHOR_EMAIL:-}" ]; then
    echo "Error: GIT_AUTHOR_NAME and GIT_AUTHOR_EMAIL must be set in .git-author." >&2
    return 1 2>/dev/null || exit 1
fi
