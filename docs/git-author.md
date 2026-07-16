# Git author for agent commits

Agent-created commits should use the correct author and committer — not the machine login.

## Setup (once per developer)

```bash
cp .git-author.example .git-author
```

Edit `.git-author` with your name and email:

```bash
GIT_AUTHOR_NAME=Your Name
GIT_AUTHOR_EMAIL=you@example.com
GIT_COMMITTER_NAME=Your Name
GIT_COMMITTER_EMAIL=you@example.com
```

`.git-author` is gitignored. Each developer keeps their own copy.

## Usage

### Bash / Git Bash

```bash
source ./scripts/git-author-env.sh
git commit -m "your message"
```

### PowerShell (agent / manual)

```powershell
# Read values from .git-author, then:
$env:GIT_AUTHOR_NAME = "Your Name"
$env:GIT_AUTHOR_EMAIL = "you@example.com"
$env:GIT_COMMITTER_NAME = "Your Name"
$env:GIT_COMMITTER_EMAIL = "you@example.com"
git commit -m "your message"
```

### Fix author on recent commits

```bash
source ./scripts/git-author-env.sh
git rebase HEAD~3 --exec "git commit --amend --no-edit --reset-author"
```

## Agent

Cursor reads `.cursor/rules/git-commit-author.mdc` and:

- loads `.git-author` before git operations
- writes plain commit messages only — **no git trailers** (`Co-authored-by`, `Signed-off-by`, tool attribution, etc.)
