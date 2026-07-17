# Automated Versioning

## Trigger behavior

- The workflow runs on every push to `main`.
- The workflow also runs on pull requests targeting `main` in dry-run mode.

## Tag formats

- Full version tag format: `v<major>.<minor>.<patch>` (for example `v2.1.8`).
- Major moving tag format: `v<major>` (for example `v2`).
- Only tags with the `v` prefix are treated as semantic version tags.

## Increment strategy

- The versioning logic scans existing tags that match `^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`.
- If no semantic version tags exist, the first tag is `v0.1.0`.
- Otherwise, the globally highest semantic version is selected and only `patch` is incremented.
- `major` and `minor` are never auto-incremented.
- Tags with leading zeros in any numeric component (for example `v1.02.3`) are ignored.

## Monotonicity rule

- Versions are globally monotonically increasing across all major lines.
- Gaps are allowed.
- Skipped major lines or missing versions are allowed.

## Moving major tag behavior

- After creating `v<major>.<minor>.<patch>`, the workflow force-updates `v<major>` to point to that tag.
- Example: creating `v3.4.10` also moves `v3` to the same commit.

## Recursion protection

- Tag pushes do not retrigger the workflow because it listens only to branch pushes on `main`.
- The workflow also ignores push events initiated by `github-actions[bot]`.
- Pull request runs are side-effect free (dry-run only).
- Pull request runs use read-only repository contents permission; only the push job on `main` receives write permission for tag updates.

## Dry-run behavior (pull requests)

- On pull requests, the workflow computes:
  - the next full version tag,
  - the major moving tag,
- and reports both values in the step summary.
- No tag creation and no tag push happen in pull request runs.

## Idempotency behavior

- Before mutating tags on pushes to `main`, the workflow checks whether the computed full version tag already exists on `origin`.
- If the tag already exists, the workflow exits successfully and makes no changes.

## Operational examples

### Example A: first run

Existing tags: _(none)_  
Computed next full tag: `v0.1.0`  
Computed major tag: `v0`  
Push mode action: create `v0.1.0`, move `v0` to it.

### Example B: normal patch increment

Existing semantic tags:

```text
v0.1.0
v0.1.1
v1.0.0
v1.0.7
```

Computed next full tag: `v1.0.8`  
Computed major tag: `v1`

### Example C: idempotent rerun

Computed next full tag: `v2.3.5`  
`origin` already has `v2.3.5`  
Result: success with no tag mutation.

### Example D: pull request dry-run

On a PR, the workflow reports:

- would create `v4.0.3`
- would move `v4`

Result: no tag is created or pushed.
