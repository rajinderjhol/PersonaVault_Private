# Manual API Integration Tests

These scripts require a running PersonaVault server at http://localhost:8000
and an authenticated session (cookie written to `cookies.txt`).

They are NOT part of the pytest suite. They are ad-hoc smoke tests for
manual verification during development.

Run: `bash tests/manual/api/test_auth.sh`
