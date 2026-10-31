# DIGI SURAKSHA — Detect. Defend. Report.

A locally runnable bilingual digital safety MVP for Indian citizens. No account, model download or paid API is required for the core application.

Developed by **ARK Team of MC² (MCTE Coding Club)**. Theme: **Digital Safety and Cyber Fraud Awareness**. License: [MIT](LICENSE).

## Submission checklist

| Requirement | Repository material |
| --- | --- |
| Complete source code | `app/`, `run.py`, dependency manifests |
| Setup and environment variables | This README and [`.env.example`](.env.example) |
| Technical design and architecture | [`docs/TECHNICAL_DESIGN.md`](docs/TECHNICAL_DESIGN.md) |
| Sample data and demo walkthrough | [`data/examples/README.md`](data/examples/README.md) |
| Automated test cases and results | [`tests/`](tests/) and [`TEST_RESULTS.md`](TEST_RESULTS.md) |
| Detection measurement | [`scripts/evaluate.py`](scripts/evaluate.py), [`data/quality_report.json`](data/quality_report.json) |
| Open-source license / external materials | [`LICENSE`](LICENSE), [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) |
| CI definition | [`.github/workflows/tests.yml`](.github/workflows/tests.yml) |

**Working prototype:** run this repository locally at `http://127.0.0.1:8000`. This is a local demonstration address, not a publicly hosted deployment. The prototype includes actual rule-based detection, OCR and draft preparation; optional model inference is not configured by default. It never files complaints or sends email for you.


## Inspected baseline

The workspace contained only an empty, clean Git repository. Windows, Python 3.11.9 and Tesseract were available; there was no application, virtual environment, test suite or configured model to preserve. Global dependencies were inconsistent, so this project uses an isolated `.venv`. Tesseract has `eng` and `osd`; Hindi OCR data is not installed.

## Install and run (Windows PowerShell)

```powershell
# Open the cloned or downloaded repository folder first.
cd digi-suraksha
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-lock.txt
.\.venv\Scripts\python run.py
```

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/docs. After setup the single run command is `.\.venv\Scripts\python run.py`. Activation is optional (`.\.venv\Scripts\Activate.ps1`, then `python run.py`). `requirements.txt` lists supported dependency ranges; `requirements-lock.txt` records the tested environment. Stop with Ctrl+C. API docs use CDN assets and require internet; the citizen UI and bundled educational material do not.

## Requirements and Linux/macOS setup

Python **3.11** is the tested version. The core app requires no GPU. Tesseract must be installed separately for screenshot OCR and available in PATH; text, URL and email analysis remain usable without OCR. English language data is required for the screenshot sample; optional Hindi language data enables `eng+hin`. No model weights or paid API subscription are required.

From a cloned/extracted repository on Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python run.py
```

On Ubuntu/Debian, the optional OCR test prerequisites are `tesseract-ocr` and `fonts-dejavu-core` (and `tesseract-ocr-hin` for Hindi OCR). Check your Tesseract distribution's installation instructions on other systems. Run from the repository root; no database migration or manual table setup is required. SQLite files are created automatically and should remain private.

## Environment variables

All variables are optional. **The application reads process environment variables, not `.env` files.** Copying `.env.example` to `.env` does not enable a provider. Never put actual keys into tracked files.

| Variable | Purpose | Default / behavior |
| --- | --- | --- |
| `REMOTE_AI_URL` | Full compatible chat-completions endpoint | Unset: disabled; configured remote use still requires UI consent |
| `REMOTE_AI_KEY` | Remote provider bearer key, if required | Unset: no secret configured; never commit |
| `REMOTE_AI_MODEL` | Remote provider model identifier | Adapter falls back to `local`; set an explicit provider model |
| `LOCAL_AI_URL` | Full loopback chat-completions endpoint | Unset: disabled; example `http://127.0.0.1:8080/v1/chat/completions` |
| `LOCAL_AI_MODEL` | Local server model name | `local` |

Default startup binds to `127.0.0.1:8000`. Server configuration is intentionally local; public exposure requires separate security work. Third-party PIN lookup is a separate, explicit online action and is not controlled by the AI variables.

## Implemented architecture and features

A modular FastAPI/Pydantic monolith serves HTML, CSS and vanilla JavaScript. Services separate deterministic detection, optional AI interpretation and SQLite incident persistence. JSON files contain bilingual UI, advisories and reporting destinations.

- Five responsive module routes, English/Hindi selection persisted locally.
- Plain text/SMS, explicit URLs, auto-detection and pasted emails; `.eml` parsing with sender, reply-to, subject and authentication-result extraction. Missing authentication results alone are not indicators.
- PNG/JPEG/WEBP screenshots through actual Tesseract OCR; extracted text is shown for review. 5 MB upload and 12-million-pixel limits. Detection uploads are not executed or persisted; separately saved incident evidence follows the opt-in storage policy below.
- Evidence excerpts, explanations, provisional risk category, separate limitations and potential impact, immediate actions and reporting route. No numeric risk score or claimed forensic proof.
- Editable complaint/email drafts, copy and TXT export controls, incident intake with date/amount/reference/evidence/acknowledgement, opt-in SQLite history and deletion. Draft generation never files a complaint or sends an email. Saved history captures the generated draft; later text-area edits are exported/copied but are not automatically saved.
- Ten searchable bilingual advisory topics available without internet while the local server is running.
- Editable `data/reporting_directory.json`, NCRP, Report Suspect and Sanchar Saathi/Chakshu destinations, provenance, verification dates and channel limitations. Official NCRP pages confirm 1930 and Report Suspect. Sanchar Saathi's homepage blocked automated fetches (403); Chakshu purpose was verified from an official DoT release, and no current time-window is asserted.

## Citizen workflow additions — 31 October 2026

AI provider and detection-engine files were left unchanged in this update.

- **Official Resources:** a bank dropdown with SBI, HDFC, ICICI, Axis and HSBC India. Entries are for customers in India, not a worldwide bank directory. Numbers, purposes, country, sources and verification dates are editable in `data/banks.json`. Source websites were checked on 31 October 2026.
- **Stay Informed:** retains all ten bundled bilingual advisories. Each includes a link to the CyberDost I4C YouTube channel; phishing and digital-arrest entries also have specific awareness-video links. Links require internet; written material remains local.
- **Advisory upload:** enter a title, original language, explanation, optional detailed guidance, HTTPS source, and optional PDF/TXT/image up to 5 MB. Uploaded material starts as pending. Open **Local advisory review**, inspect the content/source, check the review confirmation and publish. Reviewed uploads become searchable and can be removed. Original-language uploads are labelled; no AI translation is performed. Review controls are local operator controls without a separate authentication system; do not expose the app publicly. Uploaded source URLs are not fetched by the server.
- **Response Centre:** date and time are separate. Each must be supplied or explicitly marked unknown; a known time can be approximate. Drafts include these choices. State/UT, city/district, locality, sender phone and sender email are separate fields. Non-Indian prefixes receive contextual guidance, never an automatic fraud verdict.
- **PIN lookup:** the explicit online-lookup button sends only the six-digit PIN to `https://api.postalpincode.in/`, a third-party directory. Choose a returned locality and verify the suggested state/district. Manual location entry works if offline or if lookup fails. No police-jurisdiction match is claimed.
- **Evidence attachments:** up to three PNG/JPG/WEBP/PDF/TXT/EML files, 5 MB combined. Content types, signatures and image limits are checked; no malware scan is claimed. Unreadable files are rejected. Files are stored as private SQLite blobs only if Save is selected, can be downloaded from saved incident history, and are deleted with the incident or on retention cleanup. They are never automatically opened, executed or submitted externally. TXT drafts list attachment names; they do not bundle or submit evidence files. Saved files are available to anyone with access to this local app.
- **Counters:** today (IST) and cumulative incidents recorded in this app, refreshed every 30 seconds while the homepage is visible. Only deliberate Save actions count; preparing unsaved drafts and regenerating an existing saved record do not increment the counters. Start another incident creates a new record. Existing records are counted once during schema migration. After record deletion/expiry, anonymous aggregate daily counts remain. These are not government complaints or verified scam statistics.
- **Homepage/footer:** bold reporting-encouragement slogan; attribution **Developed by ARK Team of MC² (MCTE Coding Club)**. Technical storage information is on `/privacy` instead of repeated in every footer. The save label is simplified; the actual 30-day retention policy remains.
- **Try a demo:** shows a notice that a YouTube walkthrough will be posted soon. It no longer inserts sample text. No walkthrough URL has been invented.

Additional modules: `app/resources_api.py`, `app/services/{uploads,locations,advisories}.py`, `app/web/community.js`, `data/{banks,states}.json`, `tests/test_citizen_features.py`, and synthetic fixtures under `data/examples/`.

## Risk policy and limitations

Risk is a conservative rule category, not a probability: Critical = arrest/safe-account coercion plus urgency or secret solicitation; High = secret solicitation, coercion, or at least three distinct rule identifiers; Moderate = another warning indicator; Low = no configured pattern. All results are provisional. A syntactically normal URL is never certified safe.

Rules cover urgency, account/KYC pressure, secret requests, prizes, recruitment fees, investment/loan promises, authority claims and coercion, and URL scheme, IP/private host, subdomains, internationalised domains, shorteners, sensitive queries and embedded credentials. This is not comprehensive brand impersonation detection. URL destinations are never fetched or DNS-resolved. Pasted headers are not authenticated; HTML-only email text may include markup as plain evidence. Email attachments are not scanned.

## Optional AI configuration

Use an OpenAI-compatible chat-completions endpoint supporting JSON output. Configure in the shell before starting the app; `.env.example` is documentation and `.env` is not automatically loaded.

```powershell
$env:REMOTE_AI_URL = 'https://YOUR-PROVIDER/v1/chat/completions'
$env:REMOTE_AI_MODEL = 'YOUR-MODEL-ID'
# Set REMOTE_AI_KEY privately in your shell/session; never commit it.
$env:LOCAL_AI_URL = 'http://127.0.0.1:8080/v1/chat/completions'
$env:LOCAL_AI_MODEL = 'local'
.\.venv\Scripts\python run.py
```

Remote is attempted only when the user explicitly checks the disclosure/consent box. It receives matched finding snippets, not the full input, but snippets can still contain personal information. Remote failure/timeout/invalid JSON falls back to local; local failure falls back to deterministic findings. Each HTTP operation has an 8-second timeout; redirects and environment proxies are disabled. Local hostname must be loopback. Providers have a shared interface and Pydantic output validation, and unknown evidence IDs are rejected. Models cannot change risk or deterministic evidence. The model receives untrusted evidence with a system instruction to ignore embedded commands and has no tools. Structured validation cannot guarantee that prose is factually correct or follows the chosen language; treat optional AI prose as unverified.

For llama.cpp, separately run a compatible `llama-server` on loopback port 8080 with a legally obtained GGUF instruction model (`llama-server -m C:\models\model.gguf --host 127.0.0.1 --port 8080`). Nothing is downloaded automatically. RAM/VRAM requirements depend on model size, quantization and context; choose a model that fits available memory. No GPU is required for the core app/OCR. Live local/remote model inference has not been tested here because no model/provider was configured. Provider orchestration is tested with controlled failures; no fake AI output is used in normal operation. Hosting self-managed inference still has compute costs.

## Sample data and demonstration

Use [`data/examples/README.md`](data/examples/README.md) for the complete walkthrough. The directory includes labelled English/Hindi messages, a synthetic `.eml`, an actual OCR screenshot, a valid unsaved incident JSON request, and evidence/advisory text fixtures. These contain fictional data only. The sample-message file explicitly records known false positives and false negatives rather than disguising them as accuracy claims.

A simple JSON request in PowerShell:

```powershell
$payload = @{ content = 'Send OTP immediately to complete KYC'; input_type = 'text'; language = 'en'; remote_consent = $false } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/analyze' -Method Post -ContentType 'application/json' -Body $payload
```

## Tests and quality measurement

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m scripts.evaluate
```

The regression suite covers published sample fixtures, routes, locales, text/Hindi cases, URL structures, `.eml`, authentication caveats, real OCR, malformed/oversized input, consent, fallback, persistence and deletion. The 31 October expansion also covers mandatory date/time choices, attachments, cascade deletion, anonymous counters, deduplication, advisory review, bank data, and PIN lookup/failure behaviour. See `TEST_RESULTS.md` for the final run and browser verification limits.

`data/quality_report.json` records 16 manually labelled synthetic development examples (not a representative benchmark). At Moderate-or-higher as a positive warning: TP 6, TN 5, FP 3, FN 2; precision 0.667 and recall 0.750. Generic urgency produces false positives, while parcel-fee wording and some Hindi phrasing are missed. These results deliberately remain visible; do not advertise an accuracy percentage from this sample. No real citizen data is used.

## Privacy and deployment boundaries

The server binds only to 127.0.0.1. Requests have bounded bodies, uploads have bounded bytes/pixels, saved evidence attachments are stored in SQLite, content is rendered as escaped text, configured remote calls require consent, submitted URLs are never visited, and logs exclude evidence bodies. Host and write-origin checks, CSP, no-referrer and no-store headers help protect the local UI. Loopback access is not authentication: anyone with local access can read saved incidents. SQLite is unencrypted. Opt-in incidents expire after 30 days and are purged on the next history operation, not by a background timer. Deletion is logical SQLite deletion and does not guarantee forensic erasure from disk/backups. Language preference alone uses localStorage. Uploaded advisories and their optional documents are stored separately until the local operator removes them. Anonymous aggregate counts remain after incident deletion.

This MVP has no public-user authentication, rate limiting, malware scanner, threat-intelligence feed, cryptographic email authentication verification or production security review. Do not expose it on a public network. Next development: improve negation/context and multilingual evaluation, independently review the Hindi content and rule policy, install Hindi OCR data, test actual model providers, and add access control/encrypted storage before shared deployments. Validate optional model output on adversarial examples before relying on its prose.

## Troubleshooting

- OCR unavailable: install official Tesseract, add its installation folder to PATH and restart the shell/server. Run `tesseract --list-langs`. Add official `hin.traineddata` to its `tessdata` folder for Hindi OCR. The app automatically uses `eng+hin` when available, otherwise discloses the English-only limitation.
- Empty/unreadable screenshot: crop for legibility or paste the text. Upload errors are shown without internal details.
- Port 8000 busy: stop another copy of this app before launching.
- AI unavailable: the core rules still work; check environment configuration privately. No keys or provider errors are shown in the UI.
- PowerShell activation blocked: use the `.venv\Scripts\python` commands above; no execution-policy change is required.
- Clipboard blocked: select the editable draft and use Ctrl+C. Download behavior depends on the browser.

## Source manifest

The source originated in this project; the current module map is in the technical design document. Main source paths:

- `app/main.py`, `app/schemas.py`, `app/__init__.py`
- `app/services/{detection,ai,incidents}.py`, `app/services/__init__.py`
- `app/web/{index.html,style.css,app.js}`, `app/web/locales/{en,hi}.json`
- `data/{advisories,reporting_directory,quality_report}.json`
- `scripts/evaluate.py`, `tests/test_app.py`
- `run.py`, `requirements.txt`, `requirements-lock.txt`, `.env.example`, `.gitignore`, `README.md`, `TEST_RESULTS.md`

Runtime `.venv`, caches and `data/incidents.sqlite3` are ignored by Git. The database is created on the first history operation.


## Continuous integration and license

The included GitHub Actions workflow installs Python 3.11, Linux Tesseract and DejaVu fonts, installs locked dependencies, compiles Python, runs pytest and regenerates the synthetic evaluation. It requires no API credentials. GitHub-hosted CI has not been run until this repository is published; local results are recorded in `TEST_RESULTS.md`. If Tesseract or a supported font is absent locally, the OCR integration test explicitly skips; CI installs both.

Original code and project-created synthetic samples are released under the [MIT License](LICENSE). External dependencies, linked official material, videos and separately obtained model weights keep their own licenses/terms; see [third-party notices](THIRD_PARTY_NOTICES.md). Contributor guidance: [CONTRIBUTING.md](CONTRIBUTING.md).
