---
applyTo: '**'
---

## Core
- Lang: EN only (code, vars, docs)
- Func: 10–20 lines max
- Files: < 200 lines
- Folders: group by feature
- Modular: separate concerns/files
- Clean: readable, low complexity, descriptive names
- reuse funcs and avoid redundancy
- Only do requested task, be self sceptic, not suggest or assume, ask if unclear
- runnable as-is and within Docker
- .env file for sensitive configs
- config.json for non-sensitive config, data models, constants
- no hardcoding of configs, paths, URLs, keys
- microservice approach: frontend, backend, API separated
- use virtual env + requirements.txt
- avoid external dependencies unless necessary

## Naming
- Func: descriptive_snake_case
- Files: snake_case.py / kebab-case.js
- Tests: test_[module].py

## Structure
(project folder layout)
project/
├── app.py
├── config.json
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
├── UNFINISHED.md
├── functions/
│   ├── ui/
│   ├── auth/
│   ├── data/
│   └── api/
│   └── folder.md
├── templates/
│   └── folder.md
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│   └── folder.md
├── tests/{test_ui,test_auth,test_data}/
│   ├── test_ui/
│   ├── test_auth/
│   ├── test_data/
│   └── folder.md
└── utils/
    └── logger.py
│   └── folder.md

## Code
- Group similar funcs in same file
- Prefer classes
- Python <200 lines/file

## Documentation
- plain English only, alphanumeric only, no special chars
- omnipresent docstrings (Google style)
- brief, bulletpoints
- document per folder in `folder.md`, contaions: purpose, main files, sub folders dependent folders
- document per file at each file's header, contains: purpose, main funcs, dependendent files
- document per function at each function's header, contains: purpose, input data, output data, process, dependendent functions and classes
- create sections between functions and classes with clear markers within files to seperate concerns, e.g.:
    - Python: `# --- UI OPS ---`
    - HTML: `<!-- --- UI OPS --- -->`

## Logging
- plain English only, alphanumeric only, no special chars
- Use utils/logger.py
- "recursive level approach": log on each "branch" of execution tree
- use indention to indicate depth
- levels:
    - 1. Level: app start/end
    - 2. Level: func entry/exit with params
    - 3. Level: before loops/conditionals
    - 4. Level: within loops/conditionals
- Levels: DEBUG, INFO
    - DEBUG 
        - logs all levels and exception errors
        - additionally logs key variable states at key points
    - INFO:
        - logs levels 1 and 2 only and exception errors
- read debug level from .env


## Error Handling
- error must clearly state where and what the issue is
- use try/except blocks around risky operations

Pseudo Code Example:
try:
    [...]
except SpecificError as e:
  log_message(f"Error in X: {e}", level="ERROR")
  return None

## Security
- Validate/sanitize all input (bleach)
- Param queries only (SQLAlchemy)
- No raw SQL
- Add rate limiting + CSRF protection
- Sanitize filenames on upload
- Use Salt and Pepper when hashing passwords (bcrypt)

## API Resp
Format: {"status": "success|error", "data": {}, "message": ""}

## Testing
- pytest, mirror structure in /tests
- All funcs tested, ≥90% coverage
- Run `pytest --maxfail=1 --disable-warnings -q` pre-commit
- Maintain `/tests/full_test.py`:
- Uses Flask test_client for all endpoints (dummy data)
- Runs all funcs with sample inputs
- Mocks external APIs (responses/unittest.mock)
- Dummy data in `/tests/data/`
- One command: `pytest tests/full_test.py --disable-warnings -q`
- Ensure full_test.py passes before commit

## Lint/Format
- Python: PEP8 (black)
- JS: ESLint + Prettier
- Enforce via pre-commit hooks

## Frontend
- Vanilla JS ES6+, small funcs
- Use modules (import/export)
- No frameworks
- Organize by feature
- plain, compact layout

## Docs
- README.md: brief bullets points, consists of three parts:
    - purpose
    - setup as-is
    - setup in Docker
    - usage examples
- UNFINISHED.md
    - current task the AI agent is working on, prune if task is done and user confirms

## Docker
- Works local + Docker
- Include Docker configs
- Consider containerization in design

# Workflow

## Repo Management
- local git repo must exist
- commit after each task
- Commit msg: `[feat|fix|refactor|docs]: short, brief, bullet point description`

## Context Management
- At start of every iteration: Re-read copilot-instructions.md, UNFINISHED.md and README.md
- After 3 failed attempts on same task:
    1. Log "Blocked" in UNFINISHED.md
    2. Ask user for alternative approach
- On "Refresh context" command:
    1.  Reload all anchor files and restate current task + constraints

## Workflow
1. Setup folder structure + Docker
2. Config .env + config.py
3. Logging system
4. Modular funcs + tests
5. Security validation
6. Update README.md + UNFINISHED.md
8. Run full_test.py `run_tests`
9. Commit if tests pass

# IMPORTANT Global Restrictions
- No emojis
- No example text unless asked
- No removing comments
- No anticipating needs
- No globals
- No direct SQL
- No apologizing

# IMPORTANT Global Mindset
- Validate assumptions
- Assume you dont have all context
- Don’t declare “final” until user confirms
- always refer to UNFINISHED.md to prevent redundant work
- be pragmatic, concise, blunt, honest
- After EVERY user msg → re-read this file