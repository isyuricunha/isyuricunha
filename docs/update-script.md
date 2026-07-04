# `update_readme.py` Reference

The script is a single-file Python module with no package structure. It runs as a standalone script (`python update_readme.py`) and is not importable as a library.

## Module-level constants

```python
DEFAULT_FILE_ID = '1MYhLPeAoTMzpuCHDVeMbRfx-LQ16uQ92'
```

The Google Drive file ID of the quotes JSON. Used when the `QUOTES_FILE_ID` environment variable is not set.

## Functions

### `download_json()`

Downloads the quotes JSON file from Google Drive.

- Reads `QUOTES_FILE_ID` from the environment, falling back to `DEFAULT_FILE_ID`.
- Builds the URL as `https://drive.google.com/uc?id=<file_id>`.
- Calls `requests.get(file_url, timeout=10)`.
- Calls `response.raise_for_status()` - raises `HTTPError` on 4xx/5xx.
- Writes the raw response bytes to `./quotes.json`.

Error handling:

| Exception | Action |
| --- | --- |
| `requests.exceptions.Timeout` | Prints "error: request timed out while downloading quotes", exits 1 |
| `requests.exceptions.RequestException` | Prints the exception, exits 1 |
| `IOError` | Prints "error: failed to save quotes file", exits 1 |

### `read_lines_from_json()`

Reads `./quotes.json` and flattens all quote lines into a single list.

- Opens `./quotes.json` with `encoding="utf-8"`.
- Parses the JSON. The file is expected to be a list of objects, each with a `"lines"` array of strings.
- Iterates every quote and every line within it, appending to a flat list.
- Returns the list. If the list is empty, returns `["no quote available today"]` as a safe fallback.

Error handling:

| Exception | Action |
| --- | --- |
| `FileNotFoundError` | Prints "error: quotes.json file not found", exits 1 |
| `json.JSONDecodeError` | Prints the error, exits 1 |
| `Exception` (catch-all) | Prints the error, exits 1 |

The order of the catch clauses matters: `FileNotFoundError` is a subclass of `OSError` and must be caught before the generic `Exception`.

### `generate_markdown_sentence(line)`

Returns the full README markdown content as a string with the given quote line interpolated.

The template is a raw f-string that reproduces the profile bio, links, and writing sections, ending with:

```
**a sentence to brighten your day:**<br>
    {line}
```

The leading newline and indentation are part of the template and are intentional - they match the format produced by the original profile generator. The output of this function is exactly what gets written to `README.md`.

### `write_readme(text)`

Writes the generated markdown to `./README.md`.

- Opens the file in write mode with `encoding='utf8'`.
- Writes the full text.

Error handling:

| Exception | Action |
| --- | --- |
| `IOError` | Prints "error: failed to write readme file", exits 1 |

### `main()`

Orchestrates the full update process:

1. Calls `download_json()`.
2. Calls `read_lines_from_json()` to get the list of quote lines.
3. Calls `random.choice(lines)` to pick one quote.
4. Prints the selected quote (truncated to 50 chars if longer).
5. Calls `generate_markdown_sentence(line)` with the selected quote.
6. Calls `write_readme(markdown_sentence)`.

If any of the called functions exits, `main()` never reaches the next step, and `python update_readme.py` returns exit code 1. The GitHub Actions `commit and push` step then runs unconditionally, but because `README.md` was not written (or was written with the same content), the `git diff --quiet` guard prevents an empty commit.

## Entry point

```python
if __name__ == "__main__":
    main()
```

Standard Python entry point guard. `main()` is only called when the script is run directly, not when imported.

## Expected JSON format

The quotes file is a JSON list of objects. Each object may have any keys, but only `"lines"` is read:

```json
[
  {
    "lines": ["first quote line"]
  },
  {
    "lines": ["second quote line", "optional second line of the same quote"]
  }
]
```

All lines from all quotes are flattened into a single list and one is chosen at random. The script does not group lines by quote - each line is an independent candidate.

## Environment variables

| Variable | Required | Default | Used by |
| --- | --- | --- | --- |
| `QUOTES_FILE_ID` | no | `1MYhLPeAoTMzpuCHDVeMbRfx-LQ16uQ92` | `download_json()` |

No other environment variables are read. The GitHub Action sets `GITHUB_ACTOR` and `GITHUB_TOKEN` for the commit step, but those are used by the shell, not by this script.

## Concurrency and cron note

Random selection uses Python's `random.choice`, which is seeded by the system entropy source. Each workflow run picks a different quote. The schedule runs weekly, so the probability of selecting the same quote two weeks in a row is `1 / (number of unique lines)` - with 171 lines, roughly 0.58%. In that case the `git diff --quiet` guard skips the commit.
