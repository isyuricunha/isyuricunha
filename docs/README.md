# Documentation

This directory contains the full documentation for the `isyuricunha` GitHub profile repository.

## Index

| Document | Description |
| --- | --- |
| [architecture.md](./architecture.md) | Project architecture, data flow, and component overview |
| [dependencies.md](./dependencies.md) | Python dependencies, versions, and upgrade history |
| [workflow.md](./workflow.md) | GitHub Actions workflow reference |
| [update-script.md](./update-script.md) | `update_readme.py` module reference |

## Overview

`isyuricunha` is a self-updating GitHub profile repository. A scheduled GitHub Actions job generates a quote of the week - primarily via the [Ella AI agent](https://github.com/isyuricunha/ella) (small model), with a fallback to random quotes from Google Drive. The quote is written into the profile `README.md`. On tag push (`v*.*.*`), a second job creates a GitHub release with auto-generated notes.

The project is intentionally minimal: a single Python script (`update_readme.py`, used as fallback) plus a pinned `requirements.txt`. The primary path uses Ella as a composite GitHub Action - no additional code in this repo. The only external dependency is `requests`, used by the fallback to pull the quotes file from Google Drive.

## Quick Facts

- **Language**: Python 3.11
- **Runtime**: GitHub Actions (ubuntu-latest)
- **Entry point**: `update_readme.py`
- **Dependencies**: 5 (all transitive of `requests`)
- **Secrets**: `ELLA_APP_*` and `ELLA_AI_*` required for the AI path (see [workflow.md](./workflow.md)). Fallback path uses only the default `GITHUB_TOKEN`.
