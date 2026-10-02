# 🛠 Insight Bot — AI Feedback & Damage Analysis System

A production-shaped web application that automates customer damage reporting and warranty claims for CRT-eligible products. Combines **sentiment analysis** on customer feedback, **computer-vision-based damage detection** on uploaded images, and **OLTP-grade** report and claim tracking backed by PostgreSQL.

---

## 📌 Overview

When a customer receives a damaged product — or damages it themselves later — the system guides them through one of two independent workflows:

| Flow | Purpose | Table |
|---|---|---|
| **Damage Report** | Product arrived damaged (transit/manufacturer fault) | `damage_reports` |
| **Warranty Claim** | Product damaged after delivery, still under warranty | `warranty_claims` |

Both flows share product catalog data, sentiment analysis, damage analysis, and short human-readable IDs.

---

## ✨ Features

### Core Capabilities
- **Sentiment Analysis** on free-text customer feedback
- **Damage Detection** using Canny edge detection on uploaded images
- **Order Validation** against a product catalog with CRT eligibility gating
- **Warranty Policy Enforcement** — per-product warranty periods, active status, duplicate-claim prevention
- **Unique Human-Readable IDs** — `RPT-A3K9M2` for reports, `CLM-X8T4B1` for claims
- **Upsert-While-Open** — resubmissions update the same tracking ID until the report is closed
- **Image Persistence** with automatic replacement on resubmit — no orphan files
- **Full Audit Trail** — every report and claim stores image paths, timestamps, and policy snapshots

### Production-Hardened
- **Structured Logging** via Python's `logging` module
- **Typed Exception Hierarchy** (`AudioInputError`, `ImageProcessingError`, `FeedbackProcessingError`, `DatabaseError`)
- **Input Validation** — file extension whitelist, size limits, empty-field checks
- **Error Sanitization** — raw DB exceptions logged server-side; users see friendly messages
- **Double-Click Protection** — synchronous in-flight guard on the frontend + upsert on the backend
- **Collision-Resistant IDs** — 32-character alphabet (no `0/O/1/I/L`), 6 random chars, retry loop
- **Global Exception Handler** — no stack traces leak to clients

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (HTML + CSS + JS)                │
│  • Sidebar navigation                                       │
│  • 3 flows: Raise Report / Track Report / Claim Warranty    │
│  • Drag-and-drop image upload                               │
└──────────────────────────┬──────────────────────────────────┘
                           │  fetch()  (JSON + multipart)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                         │
│  • /api/damage-report       POST                            │
│  • /api/reports/{id}        GET                             │
│  • /api/warranty-claim      POST                            │
│  • /api/claims/{id}         GET                             │
│  • /api/products/{id}       GET                             │
│  • /static/*                Static file mount               │
│  • /images/damaged/*        Uploaded images                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     ┌─────────┐    ┌─────────────┐   ┌───────────────┐
     │ models/ │    │   db.py     │   │  utils/       │
     │ NLP+CV  │    │ DB queries  │   │ logging, etc. │
     └────┬────┘    └──────┬──────┘   └───────────────┘
          │                │
          ▼                ▼
┌───────────────────────────────────────────┐
│          PostgreSQL (OLTP)                │
│  • products                               │
│  • damage_reports                         │
│  • warranty_claims                        │
└───────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
deploy/
├── app.py                            # FastAPI application (web entry point)
├── main.py                           # Legacy CLI entry point (optional)
├── db.py                             # All PostgreSQL queries
├── config.py                         # Environment-driven configuration
├── schema.sql                        # DB schema + migrations
├── requirements.txt                  # Python dependencies
├── .env                              # Local secrets (git-ignored)
├── .gitignore
│
├── models/
│   ├── feedback_processor.py         # Sentiment analysis
│   ├── damage_analyzer.py            # Canny edge-based damage detection
│   ├── report_generator.py           # Structured report builder
│   ├── warranty_processor.py         # Legacy warranty helper
│   └── warranty_claim_processor.py   # Warranty policy validation + claim creation
│
├── utils/
│   ├── logger.py                     # Structured logging setup
│   ├── exceptions.py                 # Typed exception hierarchy
│   └── input_handler.py              # CLI input helper (text/voice)
│
├── templates/
│   └── index.html                    # Single-page app (sidebar + 3 flows)
│
├── static/
│   ├── css/style.css                 # Dark SaaS design system
│   └── js/app.js                     # Frontend logic
│
├── damaged_images/                   # Persisted user uploads (git-ignored)
├── uploads/                          # Temp files during processing
└── logs/                             # Runtime logs (git-ignored)
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **Database** | PostgreSQL 15+ |
| **DB Driver** | psycopg 3 |
| **Computer Vision** | OpenCV (Canny edge detection) |
| **Numerics** | NumPy |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript (ES6) |
| **Fonts** | Inter (Google Fonts) |
| **Config** | python-dotenv |

---

## 🚀 Getting Started

### Prerequisites

- Python **3.11+**
- PostgreSQL **15+** running locally
- Git

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/insight-bot.git
cd insight-bot
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the database

```bash
psql -U postgres -c "CREATE DATABASE insightbot;"
psql -U postgres -d insightbot -f schema.sql
```

Or via pgAdmin: right-click Databases → Create → Database → name it `insightbot`, then run `schema.sql` in the Query Tool.

### 5. Configure environment

Create a `.env` in the project root:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/insightbot
NEGATIVE_THRESHOLD=-0.3
LOG_LEVEL=INFO
```

Replace `YOUR_PASSWORD` with your PostgreSQL password.

### 6. Create required folders

```bash
mkdir damaged_images
mkdir uploads
mkdir logs
```

(`app.py` also creates them on startup.)

### 7. Run the application

```bash
uvicorn app:app --reload --port 8000
```

Open `http://localhost:8000` in your browser.

---

## 🔌 API Reference

All endpoints return JSON. Errors follow `{"detail": "<message>"}`.

### `GET /api/products/{order_id}` — Validate order + CRT eligibility

**Response (200):**
```json
{
  "order_id": "ORD-1001",
  "product_name": "Running Shoe X1",
  "is_crt": true,
  "warranty_status": "active"
}
```

**Errors:** `404` order not found · `400` not CRT-eligible

---

### `POST /api/damage-report` — Submit a damage report

**Multipart form fields:**

| Field | Type | Required |
|---|---|---|
| `order_id` | string | ✅ |
| `feedback` | string | ✅ |
| `image` | file | ✅ |

**Response (200) — first submission:**
```json
{
  "proceed": true,
  "tracking_id": "RPT-A3K9M2",
  "updated": false,
  "sentiment": "negative",
  "score": -0.91,
  "damage_severity": 0.42,
  "affected_area_percentage": 4.21,
  "recommendation": "Minor damage detected. Monitor condition.",
  "damaged_image_url": "/images/damaged/8f3e6c1a4b2d.jpg"
}
```

**Response (200) — resubmission (report still open):**
```json
{
  "proceed": true,
  "tracking_id": "RPT-A3K9M2",
  "updated": true
}
```

**Errors:** `404` order not found · `400` not CRT · `413` file too large · `500` internal

---

### `GET /api/reports/{tracking_id}` — Track a report

Tracking IDs follow the pattern `RPT-XXXXXX` (case-insensitive).

**Response (200):**
```json
{
  "tracking_id": "RPT-A3K9M2",
  "order_id": "ORD-1001",
  "status": "open",
  "sentiment": "negative",
  "sentiment_score": -0.91,
  "damage_severity": 0.42,
  "created_at": "2026-10-02T18:12:33.441Z",
  "damaged_image_url": "/images/damaged/8f3e6c1a4b2d.jpg"
}
```

**Errors:** `400` invalid ID format · `404` not found

---

### `POST /api/warranty-claim` — Claim warranty for post-purchase damage

**Multipart form fields:**

| Field | Type | Required |
|---|---|---|
| `order_id` | string | ✅ |
| `reason` | string | ✅ |
| `image` | file | ✅ |

**Response (200):**
```json
{
  "claim_id": "CLM-X8T4B1",
  "status": "submitted",
  "damage_severity": 0.55,
  "message": "Warranty claim submitted successfully.",
  "damaged_image_url": "/images/damaged/50c2ab85fb58.jpg"
}
```

**Errors:** `400` ineligible (warranty expired, not CRT, already claimed) · `404` order not found

---

### `GET /api/claims/{claim_id}` — Track a claim

Claim IDs follow the pattern `CLM-XXXXXX`.

---

## 🗄 Database Schema

### `products`

| Column | Type | Notes |
|---|---|---|
| `order_id` | VARCHAR(50) | PK |
| `product_id` | VARCHAR(50) | |
| `product_name` | VARCHAR(255) | |
| `customer_name` | VARCHAR(255) | |
| `purchase_date` | DATE | |
| `warranty_status` | VARCHAR(20) | `active` / `expired` / `void` |
| `is_crt` | BOOLEAN | CRT eligibility flag |
| `warranty_period_days` | INTEGER | Per-product warranty window |
| `warranty_expiry_date` | DATE | Auto-computed via trigger |

### `damage_reports`

| Column | Type | Notes |
|---|---|---|
| `tracking_id` | UUID | PK (internal) |
| `short_id` | VARCHAR(20) | Unique, user-facing (`RPT-XXXXXX`) |
| `order_id` | VARCHAR(50) | FK → products |
| `feedback` | TEXT | |
| `sentiment` | VARCHAR(20) | |
| `sentiment_score` | NUMERIC(4,3) | |
| `damage_severity` | NUMERIC(4,3) | |
| `damage_details` | JSONB | Full analysis payload |
| `damaged_image_path` | TEXT | Path in `damaged_images/` |
| `status` | VARCHAR(20) | `open` / `under_review` / `approved` / `rejected` |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | Bumped on resubmit |

**Constraint:** unique partial index on `(order_id) WHERE status = 'open'` — one open report per order.

### `warranty_claims`

| Column | Type | Notes |
|---|---|---|
| `claim_id` | UUID | PK (internal) |
| `short_id` | VARCHAR(20) | Unique, user-facing (`CLM-XXXXXX`) |
| `order_id` | VARCHAR(50) | FK → products |
| `claim_type` | VARCHAR(30) | `post_purchase` |
| `reason` | TEXT | User description |
| `damage_severity` | NUMERIC(4,3) | |
| `damaged_image_path` | TEXT | |
| `policy_snapshot` | JSONB | Warranty conditions at claim time |
| `status` | VARCHAR(20) | `submitted` / `under_review` / `approved` / `rejected` |
| `created_at` | TIMESTAMP | |

**Constraint:** unique index on `(order_id) WHERE status <> 'rejected'` — one active claim per order.

---

## 🧠 How Damage Analysis Works

The current implementation uses **Canny edge detection**:

1. Load and convert the image to grayscale
2. Run Canny edge detection (`low=100`, `high=200`)
3. Count edge pixels
4. `severity = min(1.0, edge_pixel_ratio / 0.10)`
5. `affected_area_percentage = edge_pixel_ratio × 100`

**Interpretation:**

| Severity | Recommendation |
|---|---|
| < 0.20 | Minimal or no visible damage |
| < 0.50 | Minor damage — monitor condition |
| < 0.75 | Moderate damage — consider inspection |
| ≥ 0.75 | Severe damage — recommend replacement |

> **Note on scope:** edge density is a coarse proxy for damage. In production, this would be replaced with a trained CNN classifier or a reference-image comparison. The current design keeps the pipeline offline, dependency-light, and explainable — a deliberate trade-off for this project's scope.

---

## 🎯 Business Rules

| Rule | Enforced where |
|---|---|
| Only CRT products (`is_crt = true`) proceed | `app.py` + `WarrantyClaimProcessor` |
| Warranty must be `active` | `WarrantyClaimProcessor` |
| Warranty must be within `warranty_period_days` | `WarrantyClaimProcessor` + DB trigger |
| One **open** report per order | Partial unique index + app check |
| One **active** claim per order | Partial unique index + app check |
| Rejected claims allow refiling | `WHERE status <> 'rejected'` filter |
| Resubmission updates the same report while open | Upsert logic in `create_damage_report` |
| Old image deleted on resubmit | `delete_old_image()` in `app.py` |
| Duplicate submissions absorbed | Frontend `inFlight` guard + backend upsert |

---

## 🔐 Security & Robustness

- **No secrets in code** — everything sensitive lives in `.env` (git-ignored)
- **Content validation** — file extensions whitelist, 10 MB cap, streaming writes
- **Error sanitization** — real exceptions logged; users get generic messages
- **UUID + short-ID separation** — internal PK is a UUID; public ID is short and unguessable
- **Random IDs use `secrets`** — not `random` — so they can't be predicted
- **Global exception handler** — no stack traces leak to clients
- **Typed exceptions** — failures are categorized for cleaner handling
- **SQL injection safe** — all queries use parameterized statements

---

## 🧪 Testing the Flows

### 1. Raise a damage report

```bash
curl -X POST http://localhost:8000/api/damage-report \
  -F "order_id=ORD-1001" \
  -F "feedback=The shoe arrived torn and damaged" \
  -F "image=@path/to/damaged_shoe.jpg"
```

### 2. Track it

```bash
curl http://localhost:8000/api/reports/RPT-A3K9M2
```

### 3. Claim warranty

```bash
curl -X POST http://localhost:8000/api/warranty-claim \
  -F "order_id=ORD-1005" \
  -F "reason=Laptop fell off the table" \
  -F "image=@path/to/damaged_laptop.jpg"
```

### 4. Track the claim

```bash
curl http://localhost:8000/api/claims/CLM-X8T4B1
```

Or simply open `http://localhost:8000` and walk through the UI.

---

## ⚙️ Configuration

All settings are environment-driven via `.env`:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/insightbot` | Postgres connection |
| `NEGATIVE_THRESHOLD` | `-0.3` | Sentiment score below which a report can be raised |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `LOG_DIR` | `logs` | Log output directory |

---

## 🗺 Roadmap

- [ ] Replace edge-detection with a trained CNN damage classifier
- [ ] Add admin dashboard for reviewing and approving reports/claims
- [ ] Email/SMS notifications on claim status change
- [ ] S3 + CloudFront for image storage and delivery
- [ ] Multi-image uploads per report
- [ ] Rate limiting + authentication for public deployment
- [ ] Docker + docker-compose for one-command setup
- [ ] Unit tests + integration tests (pytest)
- [ ] CI/CD via GitHub Actions

---

## 🤝 Contributing

This project started as a demo of end-to-end AI + OLTP integration. Contributions are welcome — open an issue first for substantial changes.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m "Add amazing feature"`)
4. Push (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.

---

## 👤 Author

**Your Name**
- GitHub: [@your-username](https://github.com/your-username)
- LinkedIn: [your-profile](https://linkedin.com/in/your-profile)

---

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) — modern Python web framework
- [psycopg 3](https://www.psycopg.org/psycopg3/) — PostgreSQL adapter
- [OpenCV](https://opencv.org/) — computer vision primitives
- [NumPy](https://numpy.org/) — array operations
- [PostgreSQL](https://www.postgresql.org/) — the database
- [Inter](https://fonts.google.com/specimen/Inter) — UI font

---

## 📸 Screenshots

*(Add screenshots after your next demo run — a clean capture of each flow goes a long way.)*

| Flow | Preview |
|---|---|
| Home / Raise Report | `docs/screenshots/raise-report.png` |
| Track Report | `docs/screenshots/track-report.png` |
| Claim Warranty | `docs/screenshots/claim-warranty.png` |
| API docs (`/docs`) | `docs/screenshots/swagger.png` |
