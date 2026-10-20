# Phase 3 - Refactoring and validation

Approval of all three Phase 2 reports was received before application code changes.

## Project 1 - code-smells-project

- Structure: `config/settings.py`, `views/routes.py`, `middlewares/error_handler.py`, controllers, models, and `app.py` as composition root with `create_app`.
- Security: configurable/random secret, debug opt-in, health without secrets or filesystem paths, arbitrary SQL endpoint disabled (410), reset route blocked (403), parameterized text queries and writes, initial/new user passwords hashed, password fields removed from API responses.
- Tests: `python -m unittest discover -s tests -v` - 4/4 passed; `compileall` passed. Fresh SQLite initialization verified that all three seeded user passwords are hashed.
- Boot: `python app.py` started the Flask server; live HTTP smoke test returned 200 on 10/10 representative GET endpoints, including root, products, users, orders, report, and health.

## Project 2 - ecommerce-api-legacy

- Structure: `src/app.js` composes the application; `src/models/lmsRepository.js` handles persistence; `src/controllers/lmsController.js` handles use cases; `src/views/routes.js` registers routes; configuration and error middleware are separated.
- Security: hardcoded credentials removed, passwords hashed with scrypt, and logs include only the last four card digits. Report and checkout response contracts are preserved.
- Boot: `npm start` started the server; live HTTP checks returned 200 for the financial report and checkout using the baseline short password payload. Tests: `npm test` - 2/2 passed (salted password hash, app boot, report and checkout, no full card number or gateway key in logs).
- `npm audit fix` without `--force`: 14 to 8 advisories. Final: 2 low, 1 moderate, 4 high, 1 critical. Full fix requires `sqlite3@6.0.1` (breaking major) due to the `sqlite3`/`node-gyp` dependency chain; driver migration remains pending.

## Project 3 - task-manager-api

- Structure: `create_app(test_config)` composes blueprints, extensions, configuration, and HTTP error handlers; existing `models`, `routes`, `services`, and `utils` layers remain.
- Security/quality: application and SMTP secrets from environment; Werkzeug password hashes; no password in serialization; `Session.get` replaces `Query.get`; UTC timestamps no longer use `utcnow`; productivity/category aggregation reduces report N+1 queries.
- Tests: `python -m unittest discover -s tests -v` - 2/2 passed; `compileall` passed; `seed.py` succeeded against a temporary in-memory SQLite database.
- Boot: `python app.py` started the Flask server; live HTTP smoke test checked 12 paths. Collections, reports, and health returned 200; nonexistent IDs returned expected 404; `/login` GET returned 405 because that route supports another method.

## Remaining limitations

- Project 1 still performs N+1 queries while building order item details.
- Some generic `except` blocks remain in legacy Task Manager routes.
- Eight transitive npm advisories remain until a major `sqlite3` migration is evaluated.
- Phase 2 reports preserve the original source snapshot for audit comparison; Phase 3 results are recorded here.
