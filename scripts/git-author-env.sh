#!/usr/bin/env bash
# git-author-env.sh
# Loads GIT_AUTHOR_* and GIT_COMMITTER_* environment variables from the
# .git-author file in the repository root into the current shell session.
#
# Usage (must be sourced, not executed):
#   source ./scripts/git-author-env.sh
#
# Input file:
#   .git-author  — personal identity file in the repository root (gitignored)
#                  Copy from .git-author.example and fill in your values.
#
# Exported variables:
#   GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL
#   GIT_COMMITTER_NAME (falls back to GIT_AUTHOR_NAME if not set)
#   GIT_COMMITTER_EMAIL (falls back to GIT_AUTHOR_EMAIL if not set)
#
# Exit codes:
#   0 — variables successfully exported
#   1 — .git-author not found, or required variables are missing
#
# See also:
#   .git-author.example            — template for the identity file
#   docs/git-author.md             — full setup and usage documentation
#   .cursor/rules/git-commit-author.mdc — Cursor agent rule for git identity
#   docs/scripts.md                — overview of all helper scripts

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
