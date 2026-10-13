# Neonatal Bilirubin Kramer

An educational, local-first tool for documenting the **cephalocaudal extent of visible neonatal jaundice** using qualitative Kramer zones. The primary application is a standalone browser page; a matching Python CLI supports individual observations and de-identified CSV batches.

**Clinical limitation:** Kramer zones are observations, **not bilirubin estimates or treatment thresholds**. Never use the selected zone to infer serum bilirubin concentration, Bhutani percentile, phototherapy eligibility, or neurological risk. Visual inspection can miss jaundice, including in darker skin tones. Follow age-, gestation-, and risk-factor-specific guidance with objective bilirubin measurements. Jaundice visible before 24 hours requires urgent serum bilirubin testing and clinical assessment.

## Browser application

Open [index.html](index.html) in a modern browser (or serve the repository with a static HTTP server). Select the furthest extent of jaundice observed (zone 0–5), optionally enter postnatal age in hours and gestational age in weeks, and select **Document observation**. The app displays a descriptive record and offers **Export JSON**. It works entirely on the client: **no API, external libraries, accounts, analytics, cookies, or persistent browser storage**.

The site can be hosted as static files, including on GitHub Pages, without Python, Pyodide, or a backend. Deployment URL and availability must be verified separately.

## Python installation and usage

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
python -m pytest -q
node --test tests/browser.test.cjs   # optional: Node.js 22+
```

Record a single observation or process a de-identified CSV:

```bash
python kramer.py single --zone 1 --age-hours 12 --gestational-weeks 39
python kramer.py single --json '{"zone":3,"age_hours":36,"gestational_weeks":37}'
python kramer.py batch --input sample.csv --output results.csv
```

CSV inputs require the exact header `zone` (integer 0–5); optional columns are `age_hours` (0–672) and `gestational_weeks` (22–44). Other columns are preserved. Each row receives descriptive fields (`distribution`, `early_jaundice`, `action`, `limitation`). Avoid names, MRNs, dates of birth, and other identifiable clinical information.

## Separate demonstration API

The pre-existing `agents/` and `cli.py` interfaces remain available for software experiments. They implement a **generic, unvalidated threshold-based simulation**, not neonatal bilirubin decision support. Thresholds such as primary metric >25 or secondary metric >12 are illustrative parameters **without clinical interpretation**. The conversational provider is a mock that does not perform model inference.

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py audit --task-id EX-001 --primary 10
python cli.py serve
curl http://127.0.0.1:8000/health
```

The API uses FastAPI/Pydantic and maintains an in-memory HMAC-SHA256 audit chain. The key must be supplied through the environment, never in browser code. Audit entries are signed and checked for tampering, but they are not a durable external audit system. The regex-based identifier checks are incomplete, **not HIPAA de-identification or a compliance guarantee**. The demonstration API has no user authentication: do not expose it publicly, connect it to real EHR data, or submit PHI. For experiments involving clinical data, implement appropriate authentication, access controls, retention policy, threat modeling, and governance first.

A Dockerfile and `docker-compose.yml` support running the demonstration API locally. Set a strong `AUDIT_SECRET_KEY` in a private `.env` file before using Compose.

## Scope and technology

- **Kramer zones:** 0, no visible jaundice; 1, head/neck; 2, upper trunk; 3, lower abdomen/thighs; 4, arms/lower legs; 5, palms/soles.
- **Browser:** HTML5, CSS, vanilla JavaScript. All computation remains in-browser, including JSON export.
- **Python:** standard-library assessment CLI, optional FastAPI/Pydantic simulation interface, pytest regression suite.
- **Testing:** GitHub Actions checks Python 3.10–3.13, Node.js browser logic tests, package installation, and Python compilation.
- **Compatibility:** Designed for current desktop and mobile browsers with modern JavaScript support; real-device cross-browser testing is not automated.

## Clinical sources

- [NICE CG98: Jaundice in newborn babies under 28 days](https://www.nice.org.uk/guidance/cg98/chapter/recommendations) — do not rely on visual inspection alone; early-onset jaundice needs urgent measurement.
- [American Academy of Pediatrics (2022): Management of Hyperbilirubinemia in Infants ≥35 Weeks](https://doi.org/10.1542/peds.2022-058859) — visual estimates have substantial error; measured bilirubin and age-/gestation-specific thresholds are needed.

## License

[MIT](LICENSE).
