# CampusBot — Modular Agent Harness

Lab 5, 2026 SZU International Summer Camp: *Engineering a Reliable AI Agent Product*.

CampusBot answers Shenzhen University questions in the browser using a local
model through Ollama. This repository holds the refactor of the supplied
prototype (one backend file + one prompt) into a modular Agent Harness.

## Architecture

Before — everything in one file:

```
User -> Web/API -> main.py -> Local LLM -> Response
```

After — orchestration, capability, and governance are separate:

```
User -> Web/API -> Runtime -> Skill Router -> Skill -> Local LLM -> Response
                      |
        guardrail, permissions, audit logging
```

Each request follows one fixed path in the Runtime:

```
guardrail -> route -> permission -> execute -> audit -> structured result
```

## Layout

```
project/
├── main.py              launcher entry point (thin bootstrap only)
├── api/
│   └── server.py        HTTP layer: validation and serialisation
├── runtime/
│   ├── service.py       orchestration (the order of operations)
│   └── router.py        skill selection and priority, no execution
├── skills/
│   ├── base.py          SkillResult contract shared by every skill
│   ├── campus.py        university facts
│   ├── library.py       library branches and address
│   ├── translation.py   translation only, no knowledge lookup
│   └── llm_client.py    Ollama wrapper
├── governance/
│   ├── guardrail.py     rejects prompt injection / unsafe requests
│   ├── permissions.py   role -> allowed skills
│   ├── audit.py         JSON-line execution log
│   └── middleware.py    wraps skill execution with guardrail + audit
├── tests/               38 offline tests + macOS test entry point
├── knowledge.json
└── web/                 index.html, style.css, app.js
```

`main.py` stays the entry point because the launcher always runs it. It only
starts the web service on `CAMPUSBOT_HOST` / `CAMPUSBOT_PORT`.

## Skills

Every skill exposes the same three things, so the Router does not need to know
anything about a specific capability:

```python
NAME                       # "library"
can_handle(message) -> bool
handle(message) -> SkillResult(skill, status, response)
```

`status` is `success`, `unavailable`, or `error`. Skills report failure as a
status rather than raising, and each skill only ever receives its own slice of
`knowledge.json`. When the answer is not in that slice the skill replies with a
fixed "not available" sentence, which is what makes `unavailable` distinct from
an invented answer.

### Routing order matters

The Router takes the first skill whose `can_handle()` returns true, and
`DEFAULT_SKILLS` is ordered **most specific first** (`translation`, `library`,
`campus`). The campus skill deliberately claims broad keywords such as
`university`, so with any other order these would be misrouted:

| Message | Correct skill | Misroutes to campus if ordered wrongly |
| --- | --- | --- |
| `Where is Shenzhen University Library?` | `library` | contains "university" |
| `Translate "Welcome to Shenzhen University"` | `translation` | contains "university" |

A request no skill claims is reported as `unmatched` instead of being guessed.

## Governance

| Mechanism | Behaviour |
| --- | --- |
| Guardrail | Runs *before* routing, so an injection attempt never reaches any skill. |
| Permissions | `guest` = campus only, `member` = campus/course/library/translation, `admin` = all. Unknown roles fall back to least privilege. |
| Audit log | One JSON line per request in `project/logs/audit.log`. |

The audit log records metadata only — user, skill, status, duration — never the
message text or model output:

```json
{"timestamp": "...", "user": "user01", "skill": "library", "status": "success", "duration_ms": 812.35, "detail": null}
```

## API

`POST /chat`

```json
{ "user": "user01", "role": "member", "message": "Where is the library?" }
```

```json
{
  "request_id": "67c208d2",
  "skill": "library",
  "status": "success",
  "response": "The library is ...",
  "duration_ms": 812.35
}
```

`status` is one of `success`, `unavailable`, `unmatched`, `blocked`,
`forbidden`, `error`. `user` and `role` are optional; the browser UI sends
neither and is treated as `member`, since `guest` cannot use the library and
translation demo questions.

`GET /health` returns `{"status": "ok"}`.

## Running

Double-click `Start CampusBot.cmd` (Windows) or `CampusBot Launcher.app`
(macOS). It starts the bundled Ollama, loads the model, and runs
`project/main.py`. After changing code: **Stop CampusBot**, save, and launch
again — hard-refresh the browser (Ctrl-Shift-R) for front-end changes.

The Windows launcher sets `OLLAMA_URL` (port 11435) and
`OLLAMA_MODEL=qwen3:0.6b` itself. The model is reached over `OLLAMA_URL`
(default `http://127.0.0.1:11434/api/chat`) using `OLLAMA_MODEL`. When it is
unreachable, skills return `status: "error"` with a readable message instead
of crashing the service.

## Tests

38 tests, all offline — fake skills stand in for the real ones, so no Ollama
process is required.

Windows: double-click `Run Tests.cmd`, which runs
`python -m unittest discover -s tests -p "test_*.py" -v` from `CampusBot/`.

macOS:

```bash
cd "/path/to/CampusBot-Course-macOS-arm64"
APP="$(find . -maxdepth 1 -name '*.app' -print -quit)"
CAMPUSBOT_PROJECT_ROOT="$PWD/project/tests" \
  CAMPUSBOT_SOURCE_ROOT="$PWD/project" \
  "$APP/Contents/Resources/runtime/server/CampusBotRunner/CampusBotRunner"
```

During development, from `project/`:

```bash
CAMPUSBOT_SOURCE_ROOT="$PWD" python3 tests/main.py
```

Coverage: correct routing, misroute prevention, unmatched requests, guardrail
blocking, role denial, audit record creation, contained skill crashes, and
missing knowledge surfaced as `unavailable` rather than invented.

## Lab task mapping

| Task | Where |
| --- | --- |
| 1 — Modular skills | `project/skills/` |
| 2 — Runtime integration | `project/runtime/`, `project/api/`, `project/main.py` |
| 3 — Governance | `project/governance/` |
| 4 — Automated validation | `project/tests/` |
| Bonus 1 — Structured REST contract | `api/server.py` (`request_id`, `skill`, `status`, `duration_ms`) |
| Bonus 2 — Permission control | `governance/permissions.py` |

Bonus 3 (skill composition) is not implemented.

## Dependencies

Python 3.11+ standard library plus the packages already bundled with the
launcher: FastAPI, Uvicorn, HTTPX, Pydantic. `requirements.txt` mirrors the
bundled pins so the Windows offline installer has something to read; no new
third-party packages are needed.
