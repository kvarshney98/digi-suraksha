# Verification — 15 October 2026

- Isolated Python 3.11.9 environment installed from declared dependencies; exact versions saved in `requirements-lock.txt`.
- `python -m pytest -q`: **48 passed**, zero failures. One upstream Starlette TestClient deprecation warning concerning its HTTPX integration; tests remain operational.
- `python -m compileall -q app`: passed.
- Actual Tesseract extraction from a synthetic PNG: passed and returned High risk.
- `python -m scripts.evaluate`: 16 labelled synthetic development cases; TP 6, TN 5, FP 3, FN 2, precision 0.667, recall 0.750. These are development measurements, not a population accuracy estimate. See `data/quality_report.json` for every case.
- Browser verified: English homepage, text demo and High-risk findings, Hindi selector and persisted navigation, Hindi complaint/email generation, editing draft text, copy success confirmation, advisory search, mobile menu, and rendered Swagger `/docs`.
- Layout inspected at desktop 1280×900 and mobile 390×844; mobile document width equalled viewport width (no horizontal overflow). Desktop preview: `data/home-preview.png`.
- TXT export button executed, but the in-app browser did not emit a download event. Downloaded file contents were not independently verified. Copy and editable text are available as alternatives.
- Remote/local AI failure fallback, consent gating and evidence-ID rejection tested with mocks. No real inference endpoint/model configured or tested; no API key required.
- Hindi text analysis tested; Hindi screenshot OCR not verified because only English/OSD Tesseract data is installed. Install `hin` language data to enable it.
- Financial reporting / Report Suspect verified against official NCRP pages. Chakshu purpose verified from official DoT material; homepage returned 403 to automated fetch. No claims about current Chakshu time-window eligibility.
- The app was run on loopback port 8000. No real personal data, complaint submission, email sending or external evidence transmission was used in validation.


# Citizen workflow verification — 31 October 2026

- Baseline: 48 tests passed before edits.
- Expanded suite: **81 passed**, zero failures; one pre-existing Starlette TestClient deprecation warning.
- Node syntax checks for `app/web/app.js` and `app/web/community.js`: passed. Python compile check: passed.
- Added regression coverage for required date/time versus unknown choices, approximate times, sender and location fields, file type/size/count validation, actual PNG evidence, saved downloads, attachment deletion/expiry, unsaved-file non-retention, cumulative anonymous IST counters, record-ID deduplication, advisory pending/review/publish/delete, source URL validation, bank/video data and fixed-origin PIN lookup with offline fallback.
- Browser verified: demo placeholder notice; separate date/time controls and disabling unknown values; real PIN 452001 lookup and locality choice; synthetic evidence attachment and draft filename list; Hindi draft regeneration preserving an unsaved attachment; bank dropdown and source links; advisory file upload reaching a pending queue without public publication.
- Temporary browser-test advisory was removed after verification; tests use isolated temporary databases. No real personal information or external complaint submission was used.
- Bank contacts were checked on official SBI, HDFC, ICICI, Axis and HSBC India pages. Government-channel provenance is recorded in bundled advisory data. YouTube video metadata was available through search; direct video fetches were throttled, so playback was not independently verified.
- PIN lookup is a third-party online service. A live lookup worked; tests also verify manual-entry fallback. PIN results are not an official police-jurisdiction determination.
- AI-provider and deterministic detection files retain their pre-task SHA-256 hashes; no model, provider configuration, inference order or risk policy was changed.

- Updated homepage and Response Centre checked at 390×844 and 1280×900; document width matched viewport width. Preview saved as `data/citizen-update-preview.png`.

# Open-source submission preparation — 31 October 2026

- Baseline at the start of submission preparation: **81 tests passed**.
- Added 11 fixture-driven tests for published English/Hindi messages, current false-positive/false-negative examples, sample EML, non-persistent sample incident and the actual sample screenshot through Tesseract.
- Final local result: **92 passed**, zero failures/skips; one pre-existing upstream Starlette TestClient deprecation warning.
- Python compilation and synthetic quality evaluation passed. The quality measurements remain TP 6 / TN 5 / FP 3 / FN 2 on 16 development cases; no detection policy changed in this packaging task.
- Existing OCR integration fixture now selects Windows, Linux or macOS fonts and explicitly skips if Tesseract/a supported font is missing. A Linux GitHub Actions workflow installs Tesseract/fonts and runs the full suite; hosted CI has not been run before publication.
- Added setup/environment documentation, a technical design with architecture/data flows/API/storage/security, safe demonstration fixtures, MIT license and third-party notices.
- Secret/runtime exclusions and an explicit staged-file audit precede the initial Git commit. No incident database, uploaded citizen evidence, API key, model weight or local browser capture is included in the repository.
- GitHub publication requires an authenticated account. A local commit/archive is not evidence of a successful remote upload or public deployment.
