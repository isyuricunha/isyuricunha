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
| 1 | Checkout | `actions/checkout@v7` with `GITHUB_TOKEN`, `fetch-depth: 0` |
| 2 | Setup Python | `actions/setup-python@v6`, Python 3.11, pip cache enabled |
| 3 | Install dependencies | `python -m pip install --upgrade pip` then `pip install -r requirements.txt` |
| 4 | Generate quote via Ella | `isyuricunha/ella@v1.10.2` (composite action). Fails gracefully with `continue-on-error: true` so the fallback can run. Requires `ELLA_APP_*` and `ELLA_AI_*` secrets. |
| 5 | Fallback - random quote from Drive | `python update_readme.py` (only runs if step 4 failed) |
| 6 | Commit and push | Configures git, stages `README.md`, commits only if there are changes, pushes |

### Quote generation flow

The `update-readme` job tries two paths in order:

1. **Primary (AI)**: The `generate quote via ella` step calls the [Ella](https://github.com/isyuricunha/ella) agent as a composite action. Ella detects the `schedule`/`workflow_dispatch` event, generates a short uplifting quote via the small model, rewrites the quote line in `README.md`, and commits + pushes directly. Uses `continue-on-error: true` so a failure does not abort the job.

2. **Fallback (Google Drive)**: If the Ella step fails (missing secrets, AI endpoint down, App token error), the `fallback - random quote from drive` step runs `update_readme.py`, which downloads `quotes.json` from Google Drive and picks a random quote. This preserves the pre-AI behavior as a safety net.

Both paths write the same `**a sentence to brighten your day:**<br>` format, so the commit and push step works identically regardless of which path produced the quote.

### Secrets required for the AI path

| Secret | Purpose |
| --- | --- |
| `ELLA_APP_CLIENT_ID` | GitHub App client ID for the Ella app |
| `ELLA_APP_PRIVATE_KEY` | Matching private key |
| `ELLA_AI_API_KEY` | Small model API key |
| `ELLA_AI_BASE_URL` | Small model API endpoint |
| `ELLA_AI_MODEL` | Small model name |
| `YURI_COMMIT_NAME` | Optional - overrides commit author name (defaults to "Ella Mizuki") |
| `YURI_COMMIT_EMAIL` | Optional - overrides commit author email |

If any of these are missing, the Ella step fails and the fallback runs automatically.

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
| `actions/checkout` | v7 | Repository checkout |
| `actions/setup-python` | v6 | Python toolcache setup |
| `softprops/action-gh-release` | v3 | GitHub release creation |

These are pinned to major version tags (`@v7`, `@v6`, `@v3`), not to specific commit SHAs. This is the common convention for GitHub-maintained actions and for `softprops/action-gh-release`. The v6/v7/v3 major bumps move the runtime from Node 20 to Node 24 (GitHub is force-migrating all actions off Node 20). The action inputs used by this workflow are unchanged across these major versions, so the bumps are drop-in replacements.

## Environment variables

The only variable referenced by the script is `QUOTES_FILE_ID`. It is optional - the script falls back to a hardcoded default (`1MYhLPeAoTMzpuCHDVeMbRfx-LQ16uQ92`) when it is not set. The workflow does not set it, so the default Drive file is always used.
