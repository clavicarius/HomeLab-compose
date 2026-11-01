# Automated Versioning

## Trigger behavior

- The workflow runs on every push to `main`.
- The workflow also runs on pull requests in dry-run mode.

## Tag formats

- Full version tag format: `v<major>.<minor>.<patch>` (for example `v2.1.8`).
- Only tags with the `v` prefix are treated as semantic version tags.

## Increment strategy

- The workflow delegates version calculation to
  `clavicarius/ci-platform/actions/release-semver-versioning@v1` and consumes
  its `next_tag` output. The calculation itself is maintained by that external
  action, not in this repository.
- The workflow creates and pushes the computed full version tag only. It does
  not create or move a major alias tag.

## Recursion protection

- Tag pushes do not retrigger the workflow because it listens only to branch pushes on `main`.
- The workflow also ignores push events initiated by `github-actions[bot]`.
- Pull request runs do not execute the tag-creation step.
- The workflow declares `contents: write`; tag mutation is limited by its
  event condition to pushes on `main`.

## Dry-run behavior (pull requests)

- On pull requests, the workflow reports the next full version tag in the step
  summary.
- No tag creation and no tag push happen in pull request runs.

## Idempotency behavior

- Before mutating tags on pushes to `main`, the workflow checks whether the computed full version tag already exists on `origin`.
- If the tag already exists, the workflow exits successfully and makes no changes.

## Operational examples

The push workflow first checks whether the computed tag already exists on
`origin`. If so, it succeeds without changing tags; otherwise it creates and
pushes that full version tag.
