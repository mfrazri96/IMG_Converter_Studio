# HELIX Project Memory

This file is maintained by Helix to help future agent runs understand the project quickly.

<!-- HELIX:PROJECT-MEMORY:START -->
Last updated: 2026-04-29T12:25:27.134Z
Project: Easy IMG Studio
Stack: Python project (high confidence)
Root: C:\Users\PERFIX PC\Desktop\Project Fun2\Easy IMG Converter
Package manager: npm
Scripts: none detected

Recent workflow:
- Status: completed
- Task: Convert this project from Docker-only runtime to a local localhost web app and redesign the UI to be more professional, user friendly, and polished. Goals: 1...
- Preset: auto
- Project access: Full Project Write
- Changed files: HELIX.md, web_app/cli.py, web_app/app/main.py, tests/test_web_scaffold.py, README.md, web_app/app/static/index.html, easy_img_converter/ui/main_window.py, requirements.txt, web_app/README-web.md, pyproject.toml run_web.py tests/test_web_backend.py tests/test_web_scaffold.py tests/test_web_static_ui.py web_app/__init__.py web_app/app/__init__.py web_app/cli.py
- Commands: Test-Path -LiteralPath HELIX.md | Get-Content -LiteralPath HELIX.md -Raw | Test-Path -LiteralPath README.md | Test-Path -LiteralPath package.json | rg --files | Get-Content -LiteralPath README.md -Raw, web_app/README-web.md, web_app/app/main.py, web_app/app/static/index.html | Get-Content -LiteralPath README.md -Raw | Get-Content -LiteralPath web_app\app\static\index.html -Raw`,`Get-Content -LiteralPath web_app\app\main.py -Raw`,`Get-Content -LiteralPath tests\test_web_static_ui.py -Raw`,`Get-Content -LiteralPath tests\test_web_bac...

QA / focus:
- Blocker: Automated tests are not green; acceptance should not pass until the two unittest failures are fixed.

How to run:
- cd "C:\Users\PERFIX PC\Desktop\Project Fun2\Easy IMG Converter"
- python -m pytest
- python -m compileall .

Role backends:
- All roles inherit the workflow backend.

Tool access:
- Figma: read-only; MCP configured; ux-designer
- Playwright Browser: safe-write; Playwright connected (22 tools); tester
- GitHub: safe-write; Docker AI MCP Gateway connected (40 tools); devops
- Docker: safe-write; Docker AI MCP Gateway connected (1 tools); devops
- Database: safe-write; access configured; database
- Postman API: safe-write; access configured; tester
- Monitoring: read-only; access configured; monitor

Worker notes:
- Product Strategist (completed): Defined MVP strategy for localhost runtime, Docker preservation, UI polish, docs, and QA verification.
- Ux Designer (completed): Defined the UX handoff for the local web app redesign without editing files.
- Solution Architect (completed): Recommended a simple FastAPI localhost architecture that preserves Docker and current workflows.
- Project Planner (completed): Planned backend, frontend, docs, and QA tasks for localhost runtime plus UI polish.
- Project Scaffolder (completed): Verified the Python/FastAPI localhost scaffold and updated HELIX with current verification status.
- Backend (completed): Backend localhost runtime hardening is complete with focused tests and docs updates.
- Frontend (completed): Frontend UI polish and docs updates are complete; checks pass except dependency-blocked localhost launch.
- QA Specialist (repaired): QA found localhost/browser flow works, but automated tests and HELIX docs are not acceptance-ready.
<!-- HELIX:PROJECT-MEMORY:END -->
