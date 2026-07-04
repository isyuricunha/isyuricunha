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
            ┌─────────────────────────────┐
            │   update_readme.py          │
            │                             │
            │   1. download_json()        │──► Google Drive (quotes.json)
            │   2. read_lines_from_json() │──► quotes.json (local file)
            │   3. random.choice(lines)   │
            │   4. generate_markdown()    │
            │   5. write_readme()         │──► README.md
            └──────────────┬──────────────┘
                           │ git commit + push
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

```
Google Drive file (ID: 1MYhLPeAoTMzpuCHDVeMbRfx-LQ16uQ92)
    │
    │  GET https://drive.google.com/uc?id=<id>
    ▼
quotes.json  (list of objects, each with a "lines" array)
    │
    │  flatten all "lines" into one list
    ▼
random.choice(lines)  →  single quote string
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

- **`GITHUB_TOKEN`**: the default token provided by GitHub Actions. Used for the commit-and-push step. No custom secrets are required.
- **`contents: write`**: only requested by the `create-release` job, which needs it to publish a release.

## Failure Modes

| Failure | Behavior |
| --- | --- |
| Google Drive unreachable or file deleted | `download_json()` catches `Timeout` / `RequestException`, prints an error, exits 1 |
| Invalid JSON in the quotes file | `read_lines_from_json()` catches `json.JSONDecodeError`, exits 1 |
| Empty quotes list | Returns `["no quote available today"]` instead of failing |
| README write fails (disk full, permissions) | `write_readme()` catches `IOError`, exits 1 |

When the script exits non-zero, the `commit and push` step is skipped, so the profile README keeps its previous content.
