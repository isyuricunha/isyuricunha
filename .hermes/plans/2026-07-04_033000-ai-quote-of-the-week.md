# AI Quote of the Week (cron mode) - Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task. This plan is self-contained and assumes the implementer has zero context about either repo.

**Goal:** Add a `quote` mode to the Ella agent so that a scheduled GitHub Action can trigger her to generate a fresh "quote of the week", rewrite the quote line in the profile repo's `README.md`, and commit + push it - with no issue, no comment, and no manual trigger.

**Architecture:** A single new mode `quote` in Ella's dispatch table. The profile repo (`isyuricunha/isyuricunha`) runs a weekly cron that simply calls Ella as a composite GitHub Action in `workflow_dispatch` (or `schedule`) context. Ella detects the event, loads the current `README.md`, asks the small model for one short uplifting sentence, rewrites the quote line, commits, pushes. The existing `update_readme.py` (Google Drive random quotes) stays as a fallback step that only runs if Ella's step fails.

**Tech Stack:** Python 3.10+, single-file `agent.py` (~2600 lines), `urllib` for AI calls (no third-party deps), `gh` and `git` CLI for git operations, GitHub Actions composite action, GitHub App token auth (`actions/create-github-app-token@v3`).

---

## Two repos involved

- **Ella repo** (where the AI lives): `/home/cloud/github/ella` - remote `github.com/isyuricunha/ella`. All code changes for the AI capability happen here.
- **Profile repo** (where the quote lands): `/home/cloud/github/isyuricunha` - remote `github.com/isyuricunha/isyuricunha`. Only workflow + secret changes happen here.

The implementer works in BOTH repos. Each task says which repo it touches. Commit per task, in the repo the task changed.

## Key facts about Ella's current code (verified line numbers)

These are the anchor points in `/home/cloud/github/ella/.ella/agent.py` that the plan edits. Line numbers are from the current `master` branch; re-read before editing to confirm.

- **`__init__` (`:407-454`)**: reads `GITHUB_EVENT_PATH`, builds `self.event`, sets `self.repo`, `self.issue_number`, `self.comment_id`, `self.is_pr`, `self.default_branch = self.event["repository"]["default_branch"]`. **THIS LINE CAN CRASH** on a `schedule` event payload - see Task 1.
- **`run()` (`:456-486`)**: the owner-ACL guard is gated by `if self.comment_id:` (`:460`), so it is SKIPPED for schedule/workflow_dispatch - safe, no change needed.
- **`parse_command()` (`:708-765`)**: decides `self.mode` from `GITHUB_EVENT_NAME`. Has branches for `issues`, `workflow_run`, `pull_request*`. **No branch for `schedule` or `workflow_dispatch`** - falls through to the comment-body regex parse, which finds nothing in a schedule payload, leaving `self.mode = "unknown"`. We add a branch here.
- **`_dispatch` (`:677-689`)**: `dict[str, callable]` mapping mode -> handler. Add `"quote": _handle_quote`.
- **`_handle_read_only` (`:540`)**: template for a small-model-only handler. We do NOT reuse it directly because `quote` also needs to write a file + commit + push, but we lift its `ai_call` shape.
- **`handle_read_only` (`:1040`)**: builds messages, calls `self.ai_call(messages, MAX_TOKENS[self.mode], use_small=True)`, returns the string. Copy this pattern.
- **`system_prompt_for_read_only` (`:1107`)**: per-mode system prompts. We do NOT add a branch here; the quote system prompt lives inside `_handle_quote` to keep it self-contained (it's not an "answer" mode).
- **`ai_call` (`:1405`)**: `self.ai_call(messages, max_tokens, tools=None, use_small=False)`. For quote we pass `use_small=True` and a small `max_tokens`.
- **`MAX_TOKENS` (`:112-123`)**: dict mapping mode -> env-tunable token cap. Add `"quote": env_int("ELLA_MAX_TOKENS_QUOTE", 120)`.
- **`git()` (`:224`)** and **`gh()` (`:219`)**: the CLI wrappers. Reuse for commit/push.
- **`commit_and_push_fix` (`:2327`)**: the reference commit pattern. Our `_handle_quote` does a SIMPLER version (single known file `README.md`, fixed commit message `"update week quote"`, push to default branch). Do NOT reuse the method directly - it depends on `self.pr_info` which doesn't exist in quote mode. Lift the git config + add + commit + push calls.
- **`commit_name` / `commit_email` (`:446-450`)**: already defaulted to `"Ella Mizuki"` / the bot noreply email. Override via `YURI_COMMIT_NAME` / `YURI_COMMIT_EMAIL` env if set. Reuse as-is.
- **`defaults` dict (`:749`)**: mode -> default prompt when user gave none. Add a `quote` default.
- **`help_text` (`:779`)**: the `/ella help` text. Add a `quote` entry (harmless even though quote isn't a slash command - documents the mode).
- **`tests/test_agent.py`**: existing test file uses `importlib` to load `agent.py` and `_make_ella_shell()` (`:28`) to build an `Ella` without `__init__`. Follow this exact pattern for quote tests.

## Key facts about the profile repo

- **`.github/workflows/main.yml`**: current workflow. Has two jobs: `update-readme` (cron weekly `0 0 * * 0`, runs `python update_readme.py`, commits), and `create-release` (on tag push).
- **`update_readme.py`**: downloads `quotes.json` from Google Drive, `random.choice(lines)`, writes `README.md`. The quote line it produces has this EXACT format (lines 80-110):
  ```
  **a sentence to brighten your day:**<br>
      {line}

  ```
  Ella's `_handle_quote` MUST reproduce this exact block so the two writers are interchangeable.
- **`requirements.txt`**: just `requests` + transitive deps. No change needed (Ella is called as an action, not pip-installed here).

## The quote line format (must be byte-identical to the existing writer)

The current `README.md` ends with:

```
**a sentence to brighten your day:**<br>
    feel the fear and do it anyway

```

(two trailing newlines, the quote indented by 4 spaces, no trailing period). The replacement must preserve everything BEFORE the `**a sentence to brighten your day:**` marker and swap only the indented quote line. Detection strategy: split the README on the marker `**a sentence to brighten your day:**<br>`, keep everything before it + the marker, then append `\n    {quote}\n\n`.

## Open questions the user has already answered (do not re-litigate)

1. Architecture: cron-direct (no issue, no comment). Confirmed.
2. Fallback: keep `update_readme.py` as backup.
3. Cadence: weekly, unchanged.
4. Target README lives in the profile repo where the workflow runs.
5. Echo the prompt / tunable: NOT required for v1 - prompt hardcoded in the handler. (If later wanted, add `ELLA_QUOTE_PROMPT` env override as a follow-up.)

## Still-open decisions to confirm at execution time

- **Ella action ref**: pin to a tag once Task 6 ships a release tag, never `@main`. Until the tag exists, the profile repo task uses a placeholder and is the LAST task.
- **Profile repo secrets**: must be added by the user (not the implementer) - `ELLA_APP_CLIENT_ID`, `ELLA_APP_PRIVATE_KEY`, `ELLA_AI_API_KEY`, `ELLA_AI_BASE_URL`, `ELLA_AI_MODEL`, `YURI_COMMIT_NAME`, `YURI_COMMIT_EMAIL`. The implementer CANNOT add secrets; the user does it in the repo settings UI.

---

## Phase 1 - Ella gains the `quote` mode (Ella repo)

All tasks in this phase edit `/home/cloud/github/ella` unless noted.

### Task 1: Defend `__init__` against schedule-event payloads

**Objective:** Make `Ella.__init__` not crash when `GITHUB_EVENT_NAME` is `schedule` (whose payload may lack `repository.default_branch` on some runner versions).

**Files:**
- Modify: `/home/cloud/github/ella/.ella/agent.py:427`
- Test: `/home/cloud/github/ella/tests/test_agent.py` (extend)

**Step 1: Write failing test**

Append to `tests/test_agent.py` a new test class that builds an `Ella` with a schedule-shaped event (no `repository.default_branch`) and asserts `__init__` does not raise. Use the existing `_make_ella_shell` style - construct `object.__new__(agent.Ella)` and call a minimal init, OR refactor: easier path is to test the defensive line directly.

Practical test (add to `tests/test_agent.py`):

```python
class TestInitSchedulePayload:
    def test_default_branch_missing_does_not_crash(self, monkeypatch, tmp_path):
        # schedule events include repository but be defensive anyway
        import json
        event = {"repository": {}}  # no default_branch key
        p = tmp_path / "event.json"
        p.write_text(json.dumps(event))
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(p))
        monkeypatch.setenv("GITHUB_REPOSITORY", "isyuricunha/isyuricunha")
        obj = agent.Ella()  # must not raise
        assert obj.default_branch in ("master", "main")
```

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_agent.py::TestInitSchedulePayload -v`
Expected: FAIL - `KeyError: 'default_branch'` (or similar).

**Step 3: Write minimal implementation**

Edit `/home/cloud/github/ella/.ella/agent.py:427`:

Old:
```python
self.default_branch = self.event["repository"]["default_branch"]
```

New:
```python
repo = self.event.get("repository", {}) or {}
self.default_branch = repo.get("default_branch") or "master"
```

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_agent.py::TestInitSchedulePayload -v`
Expected: PASS.

**Step 5: Run the full suite to confirm no regression**

Run: `python3 -m pytest tests/ -v`
Expected: all existing tests still PASS.

**Step 6: Commit**

```bash
cd /home/cloud/github/ella
git add .ella/agent.py tests/test_agent.py
git commit -m "fix: tolerate schedule event payloads in Ella init"
```

---

### Task 2: Add `quote` to `MAX_TOKENS` and command defaults

**Objective:** Register the `quote` mode in the token-cap dict and give it a default prompt.

**Files:**
- Modify: `/home/cloud/github/ella/.ella/agent.py:112-123` (MAX_TOKENS) and `:749-762` (defaults)

**Step 1: Write failing test**

Add to `tests/test_agent.py`:

```python
class TestQuoteModeRegistration:
    def test_quote_in_max_tokens(self):
        assert "quote" in agent.MAX_TOKENS
        assert agent.MAX_TOKENS["quote"] >= 60
```

**Step 2: Run, verify FAIL**

Run: `python3 -m pytest tests/test_agent.py::TestQuoteModeRegistration -v`
Expected: FAIL - KeyError 'quote' (the env_int resolves at import, so the dict lacks the key).

**Step 3: Implement**

Edit `/home/cloud/github/ella/.ella/agent.py` MAX_TOKENS dict (after the `"triage"` line, `:122`):

```python
    "triage": env_int("ELLA_MAX_TOKENS_TRIAGE", 8192),
    "quote": env_int("ELLA_MAX_TOKENS_QUOTE", 120),
}
```

Edit the `defaults` dict inside `parse_command` (after `:758`):

```python
            "wiki": "Generate structured Markdown documentation for this repository.",
            "quote": "Generate a short uplifting quote of the week for a developer's GitHub profile README.",
        }
```

**Step 4: Run, verify PASS**

Run: `python3 -m pytest tests/test_agent.py::TestQuoteModeRegistration -v`
Expected: PASS.

**Step 5: Full suite**

Run: `python3 -m pytest tests/ -v` - all PASS.

**Step 6: Commit**

```bash
cd /home/cloud/github/ella
git add .ella/agent.py tests/test_agent.py
git commit -m "feat: register quote mode token cap and default prompt"
```

---

### Task 3: Add `schedule`/`workflow_dispatch` branch to `parse_command`

**Objective:** Route schedule and workflow_dispatch events to `self.mode = "quote"`.

**Files:**
- Modify: `/home/cloud/github/ella/.ella/agent.py:708-723` (parse_command top)

**Step 1: Write failing test**

Add to `tests/test_agent.py`:

```python
class TestParseCommandSchedule:
    def test_schedule_event_sets_quote_mode(self, monkeypatch, tmp_path):
        import json
        event = {"repository": {"default_branch": "master"}}
        p = tmp_path / "event.json"
        p.write_text(json.dumps(event))
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(p))
        monkeypatch.setenv("GITHUB_REPOSITORY", "isyuricunha/isyuricunha")
        monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
        obj = agent.Ella()
        obj.parse_command()
        assert obj.mode == "quote"
        assert obj.prompt  # non-empty default
```

**Step 2: Run, verify FAIL**

Run: `python3 -m pytest tests/test_agent.py::TestParseCommandSchedule -v`
Expected: FAIL - `obj.mode == "unknown"` after parse_command (no schedule branch).

**Step 3: Implement**

Edit `/home/cloud/github/ella/.ella/agent.py` `parse_command` - add a new branch right after the `workflow_run` branch (currently `:715-718`) and before the `pull_request` branch (`:720`):

```python
        if event_name == "workflow_run" and self.event.get("action") == "completed":
            self.mode = "heal"
            self.prompt = ""
            return

        if event_name in {"schedule", "workflow_dispatch"}:
            self.mode = "quote"
            self.prompt = ""
            return

        if event_name in {"pull_request", "pull_request_target"} and self.event.get("action") in {"opened", "synchronize"}:
```

The `defaults` dict (already edited in Task 2) fills `self.prompt` at the bottom of `parse_command` when it's empty (`:761-762`).

**Step 4: Run, verify PASS**

Run: `python3 -m pytest tests/test_agent.py::TestParseCommandSchedule -v`
Expected: PASS.

**Step 5: Full suite**

Run: `python3 -m pytest tests/ -v` - all PASS.

**Step 6: Commit**

```bash
cd /home/cloud/github/ella
git add .ella/agent.py tests/test_agent.py
git commit -m "feat: route schedule and workflow_dispatch events to quote mode"
```

---

### Task 4: Write the `_handle_quote` method

**Objective:** The handler: read README, call small model, sanitize, rewrite quote line, commit, push. No issue, no comment.

**Files:**
- Modify: `/home/cloud/github/ella/.ella/agent.py` - add method near `_handle_read_only` (`:540`) and wire it into `_dispatch` (`:677`).

**Step 1: Write failing test**

Add to `tests/test_agent.py`:

```python
class TestHandleQuote:
    def _make_quote_shell(self, monkeypatch, tmp_path, readme_text, model_output):
        obj = agent._make_ella_shell() if hasattr(agent, "_make_ella_shell") else object.__new__(agent.Ella)
        # use the existing _make_ella_shell helper from the top of this test file
        obj = object.__new__(agent.Ella)
        obj.mode = "quote"
        obj.prompt = "Generate a short uplifting quote of the week for a developer's GitHub profile README."
        obj.repo = "isyuricunha/isyuricunha"
        obj.default_branch = "master"
        obj.commit_name = "Ella Mizuki"
        obj.commit_email = "290269138+ella-mizuki[bot]@users.noreply.github.com"
        obj.yuri_name = ""
        obj.yuri_email = ""
        obj.issue_number = -1
        obj.comment_id = 0
        obj.ai_base_url = "https://example.invalid"
        obj.ai_model = "m"
        obj.ai_api_key = "k"
        obj.ai_small_model = "m"
        obj.ai_small_base_url = "https://example.invalid"
        obj.ai_small_api_key = "k"
        # write README into the cwd tmp_path
        (tmp_path / "README.md").write_text(readme_text)
        monkeypatch.chdir(tmp_path)
        # capture git/gh calls
        calls = []
        def fake_git(args, check=True):
            calls.append(("git", args))
            return ""
        def fake_ai_call(messages, max_tokens, tools=None, use_small=False):
            calls.append(("ai_call", use_small))
            return model_output, []
        monkeypatch.setattr(agent, "git", fake_git)
        monkeypatch.setattr(obj, "ai_call", fake_ai_call)
        obj._calls = calls
        return obj

    def test_writes_quote_and_commits(self, monkeypatch, tmp_path):
        readme = "hello\n\n**a sentence to brighten your day:**<br>\n    old quote\n\n"
        obj = self._make_quote_shell(monkeypatch, tmp_path, readme, "do the thing you fear")
        agent.Ella._handle_quote.__get__(obj)() if hasattr(agent.Ella, "_handle_quote") else None
        # the method must exist & run without raising; assert README changed and git push called
        new_readme = (tmp_path / "README.md").read_text()
        assert "do the thing you fear" in new_readme
        assert "old quote" not in new_readme
        git_args = [c for c in obj._calls if c[0] == "git"]
        flat = [a for _, args in git_args for a in args]
        assert "commit" in flat
        assert "push" in flat
```

Note: the implementer may need to make `_handle_quote` a regular method on `Ella` (not a closure - the existing `_dispatch` style uses `_handle_quote` defined at class scope like the others). Adjust the test to call `obj._handle_quote()` once the method exists. See the existing `_handle_read_only` (`:540`) for the exact pattern.

**Step 2: Run, verify FAIL**

Run: `python3 -m pytest tests/test_agent.py::TestHandleQuote -v`
Expected: FAIL - `AttributeError: Ella has no _handle_quote` (or the commit/push assertions fail because the method doesn't exist yet).

**Step 3: Implement**

Add `_handle_quote` to the `Ella` class near `_handle_read_only` (after `:570`):

```python
    def _handle_quote(self) -> None:
        self.validate_ai_config()
        system = (
            "You generate a single short quote of the week for a developer's "
            "GitHub profile README. Output exactly one line, 5 to 15 words, "
            "motivational or reflective, never political or divisive. No "
            "quotation marks around it. No attribution. No markdown. No "
            "first person. Just the sentence, capitalized, no trailing period."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": self.prompt or "Generate a short uplifting quote of the week for a developer's GitHub profile README."},
        ]
        try:
            content, _ = self.ai_call(messages, MAX_TOKENS["quote"], use_small=True)
        except Exception as exc:
            print(f"AI call failed during quote: {exc}")
            return

        quote = self._sanitize_quote(content or "")
        if not quote:
            print("Quote generation produced no usable output; skipping commit.")
            return

        self._rewrite_readme_quote(quote)
        self._commit_readme()

    @staticmethod
    def _sanitize_quote(raw: str) -> str:
        # strip code fences
        s = raw.strip()
        if s.startswith("```"):
            s = s.strip("`")
            # remove possible language tag on first line
            s = "\n".join(line for line in s.splitlines() if not line.strip().startswith(("python", "text", "markdown"))).strip()
        # take the first non-empty line
        line = next((l.strip() for l in s.splitlines() if l.strip()), "")
        # strip surrounding quotes
        line = line.strip(' "“”`')
        # cap length
        if len(line) > 140:
            line = line[:137].rstrip() + "..."
        return line

    @staticmethod
    def _rewrite_readme_quote(quote: str) -> None:
        path = Path("README.md")
        readme = path.read_text(encoding="utf-8") if path.exists() else ""
        marker = "**a sentence to brighten your day:**<br>"
        new_block = f"{marker}\n    {quote}\n"
        if marker in readme:
            before = readme.split(marker, 1)[0]
            # drop everything after marker up to the trailing blank lines, then re-append
            readme = before + new_block + "\n"
        else:
            readme = readme.rstrip("\n") + "\n\n" + new_block + "\n"
        path.write_text(readme, encoding="utf-8")

    def _commit_readme(self) -> None:
        name = self.yuri_name or self.commit_name
        email = self.yuri_email or self.commit_email
        git(["config", "user.name", name])
        git(["config", "user.email", email])
        changed = git(["ls-files", "--modified", "--others", "--exclude-standard"]).splitlines()
        if "README.md" not in changed and "README.md" not in git(["status", "--porcelain"]).split():
            print("No README changes to commit.")
            return
        git(["add", "README.md"])
        git(["commit", "--no-verify", "-m", "update week quote"])
        git(["push", "origin", f"HEAD:{self.default_branch}"])
```

Then wire it into `_dispatch` (`:677-689`). Add after the `"heal"` entry:

```python
        "heal": _handle_heal,
        "quote": _handle_quote,
    }
```

**Step 4: Run, verify PASS**

Run: `python3 -m pytest tests/test_agent.py::TestHandleQuote -v`
Expected: PASS. The test's monkeypatched `git` records the `commit` and `push` calls; the README on disk contains the new quote.

**Step 5: Full suite**

Run: `python3 -m pytest tests/ -v` - all PASS.

**Step 6: Commit**

```bash
cd /home/cloud/github/ella
git add .ella/agent.py tests/test_agent.py
git commit -m "feat: add quote mode that rewrites the README and commits"
```

---

### Task 5: Cover sanitizer edge cases + failure path

**Objective:** Test the sanitizer with junk input and test that a failed AI call does NOT commit.

**Files:**
- Test: `/home/cloud/github/ella/tests/test_agent.py` (extend `TestHandleQuote`)

**Step 1: Write failing tests**

Add to `TestHandleQuote`:

```python
    def test_sanitize_strips_fences(self):
        assert agent.Ella._sanitize_quote("```\ndo the thing\n```") == "do the thing"

    def test_sanitize_strips_quotes(self):
        assert agent.Ella._sanitize_quote('"do the thing"') == "do the thing"
        assert agent.Ella._sanitize_quote('“keep going”') == "keep going"

    def test_sanitize_takes_first_line(self):
        assert agent.Ella._sanitize_quote("first line\nsecond line") == "first line"

    def test_sanitize_caps_length(self):
        long = "word " * 40
        out = agent.Ella._sanitize_quote(long)
        assert len(out) <= 140 and out.endswith("...")

    def test_sanitize_empty(self):
        assert agent.Ella._sanitize_quote("   \n\n") == ""

    def test_no_commit_on_ai_failure(self, monkeypatch, tmp_path):
        readme = "hello\n\n**a sentence to brighten your day:**<br>\n    old quote\n\n"
        obj = self._make_quote_shell(monkeypatch, tmp_path, readme, "irrelevant")
        def boom(*a, **k):
            raise RuntimeError("api down")
        monkeypatch.setattr(obj, "ai_call", boom)
        agent.Ella._handle_quote.__get__(obj)()
        # README unchanged
        assert "old quote" in (tmp_path / "README.md").read_text()
        # no git commit called
        assert not any(args[0] == "commit" for _, args in obj._calls if False)  # placeholder; tighten to check git calls
```

(Tighten the last assertion: the monkeypatched `git` from `_make_quote_shell` records all calls; assert none of them is a `commit`.)

**Step 2: Run, verify which fail**

Run: `python3 -m pytest tests/test_agent.py::TestHandleQuote -v`
Expected: the sanitizer tests pass already (Task 4 implemented them); `test_no_commit_on_ai_failure` should pass because Task 4's `_handle_quote` early-returns on exception. If any fail, fix the implementation, not the test.

**Step 3: (likely no implementation needed; if failing) fix**

If `test_sanitize_caps_length` fails, adjust `_sanitize_quote` so the cap is `len(line) > 140` -> truncate to 137 + "...". Already in Task 4's code.

**Step 4: Run, verify all PASS**

Run: `python3 -m pytest tests/ -v` - all PASS.

**Step 5: Commit**

```bash
cd /home/cloud/github/ella
git add tests/test_agent.py
git commit -m "test: cover quote sanitizer and ai-failure no-commit path"
```

---

### Task 6: Docs + help text in the Ella repo

**Objective:** Document the new `quote` mode in `docs/`, the `help_text`, and the README feature list.

**Files:**
- Modify: `/home/cloud/github/ella/.ella/agent.py:779` (help_text), `/home/cloud/github/ella/docs/commands.md`, `/home/cloud/github/ella/docs/internals.md`, `/home/cloud/github/ella/README.md`

**Step 1: edit `help_text`**

In `/home/cloud/github/ella/.ella/agent.py` `help_text` (`:779-810`), add after the `wiki` block:

```python
`/ella quote`
I generate a fresh quote of the week, rewrite the README, and commit. Triggered by scheduled workflow, not a comment.
```

(This is documentation only - the `quote` mode is not a slash command, but listing it in help_text is harmless and informative.)

**Step 2: edit `docs/commands.md`**

Add under `### Automated`:

```markdown
- **Quote of the week**: Triggered by a scheduled (cron) GitHub Action. I generate a short uplifting sentence, rewrite the quote line in the repo's `README.md`, and push the commit. No issue or comment is created.
```

**Step 3: edit `docs/internals.md`**

In the "Model Routing" table, add a row:

```markdown
| Small | `quote` | `ELLA_AI_SMALL_*` (falls back to large) |
```

In the "Execution Flow" section, add a bullet: "Trigger: also by `schedule` or `workflow_dispatch` event - routed to `quote` mode, generates and commits a README quote."

In the `_dispatch` description, add `quote` to the mode list.

**Step 4: edit `README.md`**

Add under Features:

```markdown
- 📝 **Quote of the week**: Generates a fresh, AI-written quote in the profile README on a weekly cron.
```

**Step 5: Full suite still green**

Run: `python3 -m pytest tests/ -v` - all PASS (docs changes don't break tests, the `help_text` edit is a string).

**Step 6: Commit**

```bash
cd /home/cloud/github/ella
git add .ella/agent.py docs/ README.md
git commit -m "docs: document quote of the week mode"
```

---

### Task 7: Tag a release in the Ella repo

**Objective:** Produce a tagged ref the profile repo can pin to.

**Files:** none (git operations only)

**Step 1: Confirm master is clean and tests pass**

Run: `cd /home/cloud/github/ella && python3 -m pytest tests/ -v && git status`
Expected: tests PASS, working tree clean.

**Step 2: Push master**

```bash
cd /home/cloud/github/ella
git push origin master
```

Wait for the repo's semantic-release workflow to cut a release tag, OR manually tag if semantic-release isn't wired:

```bash
# ONLY if semantic-release does not auto-tag:
git tag v0.1.0  # or next appropriate version
git push origin v0.1.0
```

**Step 3: Capture the exact ref**

Run: `cd /home/cloud/github/ella && git describe --tags --abbrev=0`
Expected: a tag like `v0.1.0` - note it for Task 8.

**No commit in this task** - it's a release step.

---

## Phase 2 - Profile repo uses Ella (profile repo)

All tasks in this phase edit `/home/cloud/github/isyuricunha` unless noted. **Prerequisite:** Task 7 produced a tag, and the user has added the secrets listed below.

### Prerequisite (user action, not implementer): add secrets

The user MUST add these to `isyuricunha/isyuricunha` > Settings > Secrets and variables > Actions:

- `ELLA_APP_CLIENT_ID`
- `ELLA_APP_PRIVATE_KEY`
- `ELLA_AI_API_KEY`
- `ELLA_AI_BASE_URL`
- `ELLA_AI_MODEL`
- `YURI_COMMIT_NAME` (optional - defaults to "Ella Mizuki")
- `YURI_COMMIT_EMAIL` (optional - defaults to the bot noreply)

The implementer cannot add these. If any are missing, the Ella step fails and the fallback (Task 10) kicks in.

### Task 8: Add Ella as the primary quote step in `main.yml`

**Objective:** Replace the `update readme with new quote` step with a call to Ella; keep the old script as a fallback.

**Files:**
- Modify: `/home/cloud/github/isyuricunha/.github/workflows/main.yml`

**Step 1: Read the current file**

Run: `cat /home/cloud/github/isyuricunha/.github/workflows/main.yml` (or `read_file`).
Note the existing structure: `update-readme` job runs `python update_readme.py` then commits.

**Step 2: Edit the `update-readme` job**

Replace the `update readme with new quote` step with two steps: one calling Ella, one (fallback) running the old script only if Ella failed. Use the structure from `ella/README.md:58-73` adapted.

The new `update-readme` job steps:

```yaml
    steps:
      - uses: actions/checkout@v7
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          fetch-depth: 0

      - name: setup python
        uses: actions/setup-python@v6
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: generate quote via ella
        id: ella
        uses: isyuricunha/ella@<TAG_FROM_TASK_7>
        if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
        with:
          ella_app_client_id: ${{ secrets.ELLA_APP_CLIENT_ID }}
          ella_app_private_key: ${{ secrets.ELLA_APP_PRIVATE_KEY }}
        env:
          ELLA_AI_API_KEY: ${{ secrets.ELLA_AI_API_KEY }}
          ELLA_AI_BASE_URL: ${{ secrets.ELLA_AI_BASE_URL }}
          ELLA_AI_MODEL: ${{ secrets.ELLA_AI_MODEL }}
          YURI_COMMIT_NAME: ${{ secrets.YURI_COMMIT_NAME }}
          YURI_COMMIT_EMAIL: ${{ secrets.YURI_COMMIT_EMAIL }}
          GITHUB_EVENT_NAME: schedule

      - name: fallback - random quote from drive
        if: steps.ella.outcome == 'failure' && (github.event_name == 'schedule' || github.event_name == 'workflow_dispatch')
        run: python update_readme.py

      - name: commit and push changes
        run: |
          git config user.name "${GITHUB_ACTOR}"
          git config user.email "${GITHUB_ACTOR}@users.noreply.github.com"
          git add README.md
          git diff --quiet && git diff --staged --quiet || (git commit -m "update week quote" && git push)
```

IMPORTANT: `GITHUB_EVENT_NAME: schedule` is set as an env var on the Ella step because composite actions inherit the workflow's event name, which for a `workflow_dispatch` trigger would be `workflow_dispatch` (also routed to `quote` by Task 3, so this is belt-and-suspenders). For a real `schedule` cron trigger it's already `schedule`. Setting it explicitly here guarantees Ella's `parse_command` sees the right event even when the job is later also used via `workflow_dispatch`.

The `create-release` job stays untouched.

**Step 3: Validate YAML**

Run: `python3 -c "import yaml; d=yaml.safe_load(open('/home/cloud/github/isyuricunha/.github/workflows/main.yml')); print('jobs:', list(d[True]['jobs'].keys()) if True in d else list(d['jobs'].keys()))"`

Note: `yaml.safe_load` parses the `on:` key as Python `True` (YAML 1.1 bool) - that's cosmetic; the real validation is GitHub's. Confirm both jobs (`update-readme`, `create-release`) are present.

**Step 4: Manual trigger to test**

Run:
```bash
cd /home/cloud/github/isyuricunha
gh workflow run "update readme and create releases"
sleep 8
gh run list --workflow="update readme and create releases" --limit 1
```

Capture the run ID, then:
```bash
gh run watch <RUN_ID> --exit-status
```

Expected: the `update-readme` job succeeds; the README on `origin/master` gets a new commit `update week quote` authored by the Ella bot (or by `${GITHUB_ACTOR}` if Ella's step failed and fallback ran).

**Step 5: Verify the commit landed**

Run: `cd /home/cloud/github/isyuricunha && git fetch -q origin master && git log --oneline origin/master -3`
Expected: a new `update week quote` commit at HEAD.

**Step 6: Commit**

```bash
cd /home/cloud/github/isyuricunha
git add .github/workflows/main.yml
git commit -m "ci: generate weekly quote via ella, keep drive fallback"
git push
```

---

### Task 9: Document the new flow in the profile repo docs

**Objective:** Update `docs/` to describe the AI quote flow and the fallback.

**Files:**
- Create: `/home/cloud/github/isyuricunha/docs/quote-flow.md`
- Modify: `/home/cloud/github/isyuricunha/docs/README.md` (index), `/home/cloud/github/isyuricunha/docs/architecture.md` (data flow), `/home/cloud/github/isyuricunha/docs/workflow.md` (jobs table)

**Step 1: write `docs/quote-flow.md`**

Content:
- Diagram: cron -> Ella action -> small model -> README rewrite -> commit + push.
- Fallback narrative: if the Ella step fails (missing secret, AI endpoint down, App token error), the `fallback - random quote from drive` step runs `update_readme.py` and the commit/push step still updates the README from `quotes.json`.
- Security note: the owner-ACL guard in `run()` (Ella `agent.py:460`) is skipped because `comment_id` is 0 on schedule events, so no owner check runs - which is safe because only someone with push access to the repo can edit the workflow that triggers the cron.

**Step 2: update `docs/README.md` index** - add `quote-flow.md` to the table.

**Step 3: update `docs/architecture.md`** - in the "Data Flow" section, add the AI path as the primary and the Drive path as "fallback (used when the AI step fails)".

**Step 4: update `docs/workflow.md`** - in the `update-readme` job's steps table, replace the single "update README" step with the two-step `generate quote via ella` + `fallback - random quote from drive`, and add a note explaining the `if: steps.ella.outcome == 'failure'` guard.

**Step 5: Commit**

```bash
cd /home/cloud/github/isyuricunha
git add docs/
git commit -m "docs: document ai quote of the week flow and fallback"
git push
```

---

### Task 10: E2E verification + fallback verification

**Objective:** Prove both paths work on the real runner.

**Files:** none (verification only)

**Step 1: E2E happy path**

Run (already done in Task 8 Step 4-5, repeated here as a focused check):
```bash
cd /home/cloud/github/isyuricunha
gh workflow run "update readme and create releases"
RUN_ID=$(gh run list --workflow="update readme and create releases" --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch $RUN_ID --exit-status
git fetch -q origin master && git log --oneline origin/master -3
```
Expected: job `update-readme` green, new `update week quote` commit on `origin/master`.

**Step 2: Fallback path**

Temporarily check the fallback by simulating Ella failure: in the repo settings, rename `ELLA_AI_API_KEY` to a bogus value (or just disable the `generate quote via ella` step by setting its `if: false` in a throwaway commit - do NOT push that). The clean way: trigger `workflow_dispatch` and watch the run; if the Ella step is skipped because secrets are missing, the fallback step runs and produces a Drive quote. Verify a commit still lands.

**Step 3: summarize**

Report which path produced the commit, the run URL, and the new README quote line.

**No commit** - verification only.

---

## Risks and mitigations

- **`GITHUB_EVENT_NAME` propagation through composite actions**: composite actions inherit the caller workflow's event name and `GITHUB_EVENT_PATH`. This is standard GitHub Actions behavior. Belt-and-suspenders: Task 8 sets `GITHUB_EVENT_NAME: schedule` explicitly on the Ella step env, which the `agent.py` `__init__` reads via `os.environ.get("GITHUB_EVENT_NAME")` at `:709`. **Verify in Task 8 Step 4** that `parse_command` actually sets `mode == "quote"` by checking the Actions log for the expected behavior (no "I do not recognize that command" comment, a README commit appears).
- **`schedule` payload may lack `repository.default_branch`**: mitigated by Task 1.
- **Two quotes in one week** (both Ella and fallback commit different quotes): mitigated by `if: steps.ella.outcome == 'failure'` on the fallback step - the fallback only runs if Ella failed, so only one writer commits per run.
- **Model produces markdown / fences / multiple lines**: mitigated by `_sanitize_quote` (Task 4 + Task 5 tests).
- **Prompt injection from the model output** breaks README rendering: mitigated by the sanitizer's length cap and markdown stripping; the quote is one plain line.
- **Ella commits as the wrong author**: `commit_name`/`commit_email` default to the bot identity; `YURI_COMMIT_*` override if the user wants commits to look like the user's. Task 8 passes both through; the implementer does not invent values.
- **Profile repo secrets missing**: the Ella step fails open, the fallback runs, the user sees a quote either way. The implementer should NOT silently invent secret values - if the user has not added them, the fallback is the safety net.
- **Ella action pinned to `@main`**: forbidden. Task 8 uses the tag from Task 7. If no tag exists yet, Task 8 is blocked until Task 7 completes.

## Decisions baked into this plan (do not re-litigate)

1. Cron-direct, no issue, no comment - confirmed by the user.
2. `update_readme.py` + Google Drive kept as fallback.
3. Weekly cadence unchanged (`0 0 * * 0`).
4. README target is the profile repo where the workflow runs.
5. Prompt hardcoded in `_handle_quote` for v1 (no `ELLA_QUOTE_PROMPT` env).
6. Small model tier for the AI call (zero cost, matches `ask`/`triage`/`label`).

## Execution order summary

1. Task 1 (Ella init defense) -> commit in ella repo
2. Task 2 (register quote mode) -> commit in ella repo
3. Task 3 (parse_command schedule branch) -> commit in ella repo
4. Task 4 (`_handle_quote` method + dispatch wire) -> commit in ella repo
5. Task 5 (sanitizer + failure tests) -> commit in ella repo
6. Task 6 (docs + help) -> commit in ella repo
7. Task 7 (tag/release) -> no commit, capture tag
8. (user adds secrets to profile repo)
9. Task 8 (profile `main.yml` Ella step + fallback) -> commit + push in profile repo
10. Task 9 (profile docs) -> commit + push in profile repo
11. Task 10 (E2E + fallback verification) -> no commit

Total: 6 commits in the Ella repo, 2 commits + push in the profile repo, 1 release tag.
