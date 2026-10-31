# Synthetic demonstration data

Every fixture in this directory was created for testing. Names, requests, domains and transaction references are fictional. Do not replace them with real citizen evidence in a public repository.

| File | Use | Expected behavior |
| --- | --- | --- |
| `messages.json` | Copy a `content` value into Detection Lab; choose its `input_type` | Contains English/Hindi scams, benign examples and explicitly documented current errors |
| `suspicious-email.eml` | Upload in Detection Lab | High; reply-to mismatch, reported authentication failures, OTP request and urgency |
| `suspicious-screenshot.png` | Upload in Detection Lab | OCR extracts synthetic banking/OTP text; expected High with working English Tesseract |
| `incident.json` | JSON body for `POST /api/incidents` or manually populate Response Centre | Editable draft; `save: false`; no complaint or email sent |
| `evidence.txt` | Attach in Response Centre | Synthetic evidence listed in draft; persistence only with Save |
| `advisory.txt` | Optional advisory upload attachment | Synthetic educational material; manual local review required before publication |

Run `python -m pytest -q` to verify fixture-driven API behavior. Open `/docs` to try the JSON endpoints interactively. For `/api/analyze`, send only `content`, `input_type`, `language` and optional `remote_consent` (false by default), not fixture labels or expected results.

## Quick demo

1. Start `python run.py` and open `http://127.0.0.1:8000/detect`.
2. Paste the first example from `messages.json` and analyse it. Review evidence and limitations.
3. Switch to Hindi and repeat using `otp-hi`.
4. Upload the `.eml` and `.png` samples. OCR needs Tesseract in PATH.
5. Open Response Centre, use synthetic date/time and description, and prepare a draft. Keep Save unchecked for a non-persistent demonstration.
6. Explore awareness and official-resource modules. Do not submit a real report for these fixtures.

Expected risk records CURRENT deterministic behavior, not ground truth. Labels and `known_limitation` distinguish false positives/negatives. A Low result is never a safety certification.
