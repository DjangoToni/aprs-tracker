# Contributing

Changes should keep aprs.fi response normalization independent from Home Assistant
and include sanitized API fixtures for every newly supported field.

1. Create a focused branch.
2. Run `python -m pytest` and `python -m ruff check .`.
3. Update documentation for user-visible behavior.
4. Open a pull request and explain the APRS packet examples used for verification.

Never include real API keys, private location histories, or personally identifying
API responses in issues or tests.
