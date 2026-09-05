# Neonatal Bilirubin Kramer

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** CAP / CLSI / ISO

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

---

## What It Does

Neonatal Bilirubin Kramer Assessment computes a points-based clinical score from patient risk factors using the Kramer dermal zones methodology. It maps transcutaneous bilirubin measurements to Bhutani nomogram risk tiers with tiered action thresholds.

The system includes:
- **Core scoring engine** (`kramer.py`): Points-based assessment with configurable thresholds
- **Enterprise agent suite** (`agents/`): Multi-worker evaluation with HMAC-SHA256 audit trail
- **FastAPI REST server** (`agents/api.py`): OpenAPI endpoints for task dispatch and audit verification
- **CLI interface** (`cli.py`): Command-line tools for single/batch assessment
- **Enrichment engines** (`enrichment.py`): Threshold-based monitoring for longitudinal tracking, EHR/FHIR integration, and alert escalation

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/neonatal-bilirubin-kramer.git
cd neonatal-bilirubin-kramer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set required environment variable
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
# Or copy .env.example to .env and edit
```

---

## Usage

### Core Scoring (kramer.py)

```bash
# Single patient assessment
python kramer.py single --age 68 --sex M --cancer 1 --comorbidity 1

# Batch CSV processing
python kramer.py batch --input sample.csv --output results.csv

# JSON input
python kramer.py single --json '{"age": 68, "sex": "M", "cancer": 1}'
```

### Enterprise CLI (cli.py)

```bash
# Run single task evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --critical

# Batch process CSV records
python cli.py batch -i sample.csv -o results.csv

# Verify HMAC audit trail integrity
python cli.py verify-audit

# Launch FastAPI REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### REST API

```bash
# Start server
python cli.py serve

# Health check
curl http://localhost:8000/health

# Dispatch task
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"task_id":"T1","target_identifier":"KEY-01","primary_metric":25.5}'

# View audit trail
curl http://localhost:8000/api/audit/logs
```

---

## Scoring Algorithm

The Kramer score is computed from five binary risk factors:

| Factor | Weight |
|:-------|:-------|
| Comorbidity | 1 |
| Lactate > 2 | 1 |
| Bilirubin > 4 | 1 |
| Effusion | 1 |
| Age > 60 | 1 |

**Tier thresholds:**
- Score <= 2: **low**
- Score <= 4: **moderate**
- Score > 4: **high**

---

## Input Data Schema

### CSV Format (for batch processing)

| Field | Description | Required |
|:------|:------------|:---------|
| `patient_id` | Patient identifier | Yes |
| `age` | Patient age in years | Yes |
| `sex` | Patient sex (M/F) | No |
| `prior_vte` | History of venous thromboembolism (1/0) | No |
| `cancer` | Active cancer diagnosis (1/0) | No |
| `immobility` | Immobility status (1/0) | No |
| `surgery` | Recent surgery (1/0) | No |

---

## Security

- **Zero-PHI Outbound Guard:** AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers from all outbound data
- **HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation (requires `AUDIT_SECRET_KEY` environment variable)
- **Input validation:** All inputs validated before processing

---

## Testing

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest -v --cov=. --cov-report=term-missing
```

---

## Docker Deployment

```bash
# Build and run with docker-compose
cp .env.example .env
# Edit .env to set AUDIT_SECRET_KEY
docker-compose up --build

# Or build manually
docker build -t neonatal-bilirubin-kramer .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key neonatal-bilirubin-kramer
```

---

## Project Structure

```
neonatal-bilirubin-kramer/
├── kramer.py              # Core scoring algorithm
├── cli.py                 # Enterprise CLI interface
├── enrichment.py          # Threshold-based monitoring engines
├── simulator.py           # High-throughput stress testing
├── sample.csv             # Sample input data
├── benchmark_dataset.json # Golden benchmark test cases
├── openapi_spec.json      # OpenAPI 3.1 specification
├── agents/
│   ├── __init__.py        # Package init
│   ├── api.py             # FastAPI REST server
│   ├── base.py            # Security, PHI guard, HMAC audit
│   ├── models.py          # Pydantic data models
│   ├── supervisor.py      # Multi-worker orchestrator
│   ├── workers.py         # Specialized evaluation workers
│   ├── llm_factory.py     # LLM provider abstraction
│   ├── learning.py        # Bayesian calibration engine
│   ├── metrics.py         # Prometheus metrics exporter
│   └── streamer.py        # WebSocket telemetry broadcaster
├── tests/
│   ├── test_kramer.py     # Core scoring tests
│   ├── test_enrichment.py # Enrichment engine tests
│   └── test_neonatal_bilirubin_kramer.py  # Full integration tests
├── web/
│   └── index.html         # Operations dashboard
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```
