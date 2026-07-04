# GitHub Actions Workflow

The project has a single workflow file: `.github/workflows/main.yml`.

## Triggers

| Event | Condition | Purpose |
| --- | --- | --- |
| `schedule` | `cron: "0 0 * * 0"` (every Sunday at 00:00 UTC) | Automatic weekly README update |
| `workflow_dispatch` | manual | Trigger a README update on demand from the Actions tab |
| `push` (tags) | `v*.*.*` | Create a GitHub release |

The schedule and manual triggers are handled by the `update-readme` job. The tag push is handled by the `create-release` job. The two jobs are mutually exclusive via `if` conditions on `github.event_name`, so a tag push never triggers a README update and vice versa.

## Job: `update-readme`

Runs only when `github.event_name` is `schedule` or `workflow_dispatch`.

### Steps

| # | Step | Action |
| --- | --- | --- |
| 1 | Checkout | `actions/checkout@v4` with `GITHUB_TOKEN` |
| 2 | Setup Python | `actions/setup-python@v5`, Python 3.11, pip cache enabled |
| 3 | Install dependencies | `python -m pip install --upgrade pip` then `pip install -r requirements.txt` |
| 4 | Update README | `python update_readme.py` |
| 5 | Commit and push | Configures git, stages `README.md`, commits only if there are changes, pushes |

### Commit and push logic

```bash
git config user.name "${GITHUB_ACTOR}"
git config user.email "${GITHUB_ACTOR}@users.noreply.github.com"
git add README.md
git diff --quiet && git diff --staged --quiet || (git commit -m "update week quote" && git push)
```

The `git diff --quiet && git diff --staged --quiet || ...` pattern means: if nothing changed, do nothing. If the README was modified, commit and push. This prevents empty commits when the random quote happens to be identical to the previous week (unlikely but possible) or when the download fails and the script exits before writing.

The commit message is always `"update week quote"`, which matches the pattern visible in the git log of this repository.

### Python version and caching

- **Python version**: `3.11` (pinned in the workflow, not in `requirements.txt`)
- **Cache**: `cache: 'pip'` - caches the pip download directory keyed on `requirements.txt` hash, so subsequent runs are faster when deps have not changed.

### Permissions

No explicit `permissions` block is set on this job. It uses the default `GITHUB_TOKEN` permissions granted to `GITHUB_ACTION`. The token is passed via `with: token: ${{ secrets.GITHUB_TOKEN }}` to the checkout action, which allows the subsequent `git push` to succeed.

## Job: `create-release`

Runs only when `github.event_name == 'push'` and the ref starts with `refs/tags/`.

### Steps

| # | Step | Action |
| --- | --- | --- |
| 1 | Checkout | `actions/checkout@v4` |
| 2 | Create release | `softprops/action-gh-release@v2` with auto-generated notes |

### Permissions

```yaml
permissions:
  contents: write
```

Required because creating a release writes to the repository's releases API, which is not included in the default read-only token scope.

### Release configuration

| Option | Value | Effect |
| --- | --- | --- |
| `generate_release_notes` | `true` | GitHub auto-generates release notes from commits since the last tag |
| `draft` | `false` | Published immediately, not as a draft |
| `prerelease` | `false` | Marked as a stable release |

## Third-party actions used

| Action | Version | Used for |
| --- | --- | --- |
| `actions/checkout` | v4 | Repository checkout |
| `actions/setup-python` | v5 | Python toolcache setup |
| `softprops/action-gh-release` | v2 | GitHub release creation |

These are pinned to major version tags (`@v4`, `@v5`, `@v2`), not to specific commit SHAs. This is the common convention for GitHub-maintained actions and for `softprops/action-gh-release`.

## Environment variables

The only variable referenced by the script is `QUOTES_FILE_ID`. It is optional - the script falls back to a hardcoded default (`1MYhLPeAoTMzpuCHDVeMbRfx-LQ16uQ92`) when it is not set. The workflow does not set it, so the default Drive file is always used.
