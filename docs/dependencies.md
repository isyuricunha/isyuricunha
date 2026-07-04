# Dependencies

This project has a single direct dependency: `requests`. The other four packages are `requests`' own transitive dependencies, pinned explicitly in `requirements.txt` for full reproducibility.

## Current Versions

| Package | Version | Type | Purpose |
| --- | --- | --- | --- |
| `requests` | 2.34.2 | direct | HTTP client used to download the quotes file from Google Drive |
| `certifi` | 2026.6.17 | transitive | Mozilla CA bundle for TLS certificate verification |
| `charset-normalizer` | 3.4.7 | transitive | Character encoding detection for HTTP responses |
| `idna` | 3.18 | transitive | Internationalized Domain Names (IDNA) support for URLs |
| `urllib3` | 2.7.0 | transitive | HTTP connection pooling and low-level transport |

All versions were verified against PyPI on 2026-07-04 and confirmed to resolve together cleanly under Python 3.11.

## How versions are pinned

Every package is pinned to an exact version (`==`) in `requirements.txt`. This means:

- `pip install -r requirements.txt` always produces the same installed set across runs.
- There are no floating ranges, so a new release on PyPI never silently changes the resolved versions.
- Upgrades are intentional and explicit - they require an edit to `requirements.txt`.

## Upgrade History

| Package | Previous | Current | Notes |
| --- | --- | --- | --- |
| `certifi` | 2024.7.4 | 2026.6.17 | Refreshed CA bundle; security relevant |
| `charset-normalizer` | 3.4.4 | 3.4.7 | Bug fixes in encoding detection |
| `idna` | 3.11 | 3.18 | Improved Unicode handling; minor API stability improvements |
| `requests` | 2.32.5 | 2.34.2 | New inline types (PEP 561), build system moved to hatchling, bug fixes |
| `urllib3` | 2.5.0 | 2.7.0 | Includes CVE-2025-50181 and CVE-2025-50182 fixes from 2.5.x line |

### Verification after upgrade

The updated `requirements.txt` was installed into a clean virtual environment and the full `update_readme.py` script was executed end-to-end:

- All five packages installed without conflicts.
- The script successfully downloaded `quotes.json` from Google Drive.
- It parsed the quotes (171 lines found), selected one randomly, and wrote `README.md`.
- No runtime errors or deprecation warnings from the dependency stack.

## Package Details

### requests (2.34.2)

The only package imported by `update_readme.py` (`import requests`). Used for a single `GET` call to Google Drive with a 10-second timeout. The script explicitly handles `requests.exceptions.Timeout` and `requests.exceptions.RequestException`.

- **Python requirement**: >=3.10
- **Repository**: https://github.com/psf/requests
- **Changelog**: https://docs.python-requests.org/en/master/community/updates/

### certifi (2026.6.17)

Provides the root CA certificate bundle that `requests` uses to verify TLS connections. Versioned by date (YYYY.M.D). Keeping this current is security-relevant because expired or missing roots can cause TLS verification failures, and new roots are added over time.

- **Repository**: https://github.com/certifi/python-certifi

### charset-normalizer (3.4.7)

Detects the character encoding of HTTP responses. An actively maintained alternative to `chardet`. Used internally by `requests` when the response `Content-Type` header does not specify a charset.

- **Repository**: https://github.com/jawah/charset_normalizer
- **Docs**: https://charset-normalizer.readthedocs.io/

### idna (3.18)

Implements IDNA 2008 and 2003 for internationalized domain names. `requests` uses it via `urllib3` when parsing hostnames in URLs.

- **Repository**: https://github.com/kjd/idna

### urllib3 (2.7.0)

The HTTP connection pool and transport layer underneath `requests`.

- **Repository**: https://github.com/urllib3/urllib3
- **Changelog**: https://urllib3.readthedocs.io/en/latest/changelog.html

## Notes on the test environment

When verifying in a shared Python environment (such as the Hermes agent host), `pip` may print warnings about `hermes-agent` requiring different pinned versions of `certifi`, `requests`, or `urllib3`. These warnings are about the host's own agent package and are unrelated to this repository's dependencies. In a clean virtualenv dedicated to this project, `pip install -r requirements.txt` produces no such warnings.
