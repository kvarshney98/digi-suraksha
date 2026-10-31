# Contributing

1. Use Python 3.11 and install `requirements-lock.txt` in a virtual environment.
2. Create a feature branch and keep changes focused.
3. Run `python -m pytest -q` and `python -m scripts.evaluate` from the repository root.
4. Update both locale files when adding UI text, and preserve language-independent API keys.
5. Add synthetic regression examples for meaningful behavior changes. Never attach real OTPs, passwords, financial credentials, victim evidence, incident databases or provider keys to issues or pull requests.
6. Document changed data provenance, network requests, persistence, retention and consent behavior.

Keep deterministic detection usable without AI. Model prose must not override risk categories or fabricate evidence. Do not fetch user-submitted URLs. Public deployment requires a separate access-control and security-hardening effort.

Contributions are accepted under this repository's MIT license. Third-party material requires appropriate permission and attribution; see `THIRD_PARTY_NOTICES.md`.
