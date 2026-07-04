# Architecture

## System Diagram

```
            ┌─────────────────────────────┐
            │   GitHub Actions (cron)      │
            │   "0 0 * * 0" (weekly, UTC)  │
            └──────────────┬──────────────┘
                           │ triggers
                           ▼
            ┌─────────────────────────────┐
            │   ubuntu-latest runner      │
            │   Python 3.11               │
            └──────────────┬──────────────┘
                           │ pip install -r requirements.txt
                           ▼
           ┌───────────────┴───────────────┐
           │                               │
           ▼                               ▼
  ┌────────────────────┐          ┌────────────────────┐
  │  Ella (AI) path    │          │  Fallback path     │
  │  (primary)         │          │  (if Ella fails)   │
  │                    │          │                    │
  │ isyuricunha/ella   │          │ update_readme.py   │
  │ @v1.10.2           │          │                    │
  │                    │          │ 1. download_json() │──► Google Drive
  │ small model call   │          │ 2. random.choice() │
  │ sanitize + rewrite │          │ 3. write_readme()  │──► README.md
  │ commit + push      │          │                    │
  └────────┬───────────┘          └────────┬───────────┘
           │                               │
           └───────────────┬───────────────┘
                           │ git commit + push (shared step)
                           ▼
            ┌─────────────────────────────┐
            │   GitHub profile README     │
            │   (rendered on profile page)│
            └─────────────────────────────┘
```

## Components

### `update_readme.py`

The single Python module that drives the entire profile update. It is designed to run inside the GitHub Actions runner and is not intended for local interactive use.

Responsibilities:

1. Download the quotes JSON from a Google Drive file ID.
2. Parse the JSON into a flat list of quote lines.
3. Pick one quote at random.
4. Render the full README markdown with the selected quote.
5. Write the result to `./README.md`.

The script calls `sys.exit(1)` on any error, which fails the GitHub Actions job and surfaces the problem in the Actions log.

### `requirements.txt`

Pinned dependencies for the script. Only `requests` is imported directly; the remaining packages are its transitive dependencies, pinned for reproducibility.

See [dependencies.md](./dependencies.md) for the full list and versions.

### `.github/workflows/main.yml`

The workflow file that defines two jobs:

- `update-readme` - runs on schedule or manual trigger, executes the script, commits and pushes the updated README.
- `create-release` - runs on tag push (`v*.*.*`), creates a GitHub release with auto-generated notes.

See [workflow.md](./workflow.md) for the full reference.

### `quotes.json` (ephemeral)

Downloaded at runtime from Google Drive. The file is listed in `.gitignore` and never committed - it exists only on the runner for the duration of the job.

The default Drive file ID is hardcoded in `update_readme.py` and can be overridden with the `QUOTES_FILE_ID` environment variable.

## Data Flow

### Primary path (AI via Ella)

```
GitHub Actions schedule / workflow_dispatch
    │
    │  triggers update-readme job
    ▼
isyuricunha/ella@v1.10.2 (composite action)
    │
    │  GITHUB_EVENT_NAME=schedule → parse_command routes to "quote" mode
    ▼
small model call (ELLA_AI_SMALL_* or ELLA_AI_*)
    │
    │  one line, 5-15 words, uplifting
    ▼
_sanitize_quote (strip fences, quotes, cap length)
    │
    │  rewrite "**a sentence to brighten your day:**<br>" line in README
    ▼
git commit -m "update week quote" && git push
    │
    ▼
GitHub profile page renders the new README
```

### Fallback path (Google Drive random)

```
Google Drive file (ID: 1MYhLPeAoTMzpuCHDVeMbRfx-LQ16uQ92)
    │
    │  GET https://drive.google.com/uc?id=<id>
    ▼
quotes.json  (list of objects, each with a "lines" array)
    │
    │  flatten all "lines" into one list
    ▼
random.choice(lines)  ->  single quote string
    │
    │  template substitution
    ▼
README.md  (markdown with bio + selected quote)
    │
    │  git commit -m "update week quote" && git push
    ▼
GitHub profile page renders the new README
```

## Secrets and Permissions

- **`GITHUB_TOKEN`**: the default token provided by GitHub Actions. Used for the commit-and-push step.
- **`ELLA_APP_CLIENT_ID` / `ELLA_APP_PRIVATE_KEY`**: GitHub App credentials for the Ella agent. Required for the AI path.
- **`ELLA_AI_API_KEY` / `ELLA_AI_BASE_URL` / `ELLA_AI_MODEL`**: Small model credentials. Required for the AI path.
- **`YURI_COMMIT_NAME` / `YURI_COMMIT_EMAIL`**: Optional - override the commit author for Ella's commits.
- **`contents: write`**: only requested by the `create-release` job, which needs it to publish a release.

If the AI-path secrets are missing, the Ella step fails gracefully (`continue-on-error: true`) and the fallback path produces the quote instead.

## Failure Modes

| Failure | Behavior |
| --- | --- |
| Ella step fails (missing secrets, AI endpoint down) | `continue-on-error: true` lets the fallback step run `update_readme.py` instead |
| Google Drive unreachable or file deleted | `download_json()` catches `Timeout` / `RequestException`, prints an error, exits 1 |
| Invalid JSON in the quotes file | `read_lines_from_json()` catches `json.JSONDecodeError`, exits 1 |
| Empty quotes list | Returns `["no quote available today"]` instead of failing |
| README write fails (disk full, permissions) | `write_readme()` catches `IOError`, exits 1 |

When the script exits non-zero, the `commit and push` step is skipped, so the profile README keeps its previous content.
