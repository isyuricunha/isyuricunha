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

`isyuricunha` is a self-updating GitHub profile repository. A scheduled GitHub Actions job downloads a collection of quotes from Google Drive, picks one at random, and writes it into the profile `README.md`. On tag push (`v*.*.*`), a second job creates a GitHub release with auto-generated notes.

The project is intentionally minimal: a single Python script plus a pinned `requirements.txt`. No build step, no server, no database. The only external dependency is `requests`, which pulls the quotes file from Google Drive.

## Quick Facts

- **Language**: Python 3.11
- **Runtime**: GitHub Actions (ubuntu-latest)
- **Entry point**: `update_readme.py`
- **Dependencies**: 5 (all transitive of `requests`)
- **Secrets**: none required (uses the default `GITHUB_TOKEN`)
