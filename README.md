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
- **Sentiment Analysis** on free-text customer feedback (NLP)
- **Damage Detection** using Canny edge detection on uploaded images
- **Order Validation** against a product catalog with CRT eligibility gating
- **Warranty Policy Enforcement** — per-product warranty periods, active status, duplicate-claim prevention
- **Unique Human-Readable IDs** — `RPT-A3K9M2` for reports, `CLM-X8T4B1` for claims
- **Upsert-While-Open** — resubmissions update the same tracking ID until the report is closed
- **Image Persistence** with automatic replacement on resubmit — no orphan files
- **Full Audit Trail** — every report and claim stores image paths, timestamps, and policy snapshots

### Production-Hardened
- **Structured Logging** via Python's `logging` module (format: `timestamp - name - level - message`)
- **Typed Exception Hierarchy** (`AudioInputError`, `ImageProcessingError`, `FeedbackProcessingError`, `DatabaseError`)
- **Input Validation** — file extension whitelist, size limits, empty-field checks
- **Error Sanitization** — raw DB exceptions logged server-side; users see friendly messages
- **Double-Click Protection** — synchronous in-flight guard on the frontend + upsert on the backend
- **Collision-Resistant IDs** — 32-character alphabet (no `0/O/1/I/L`), 6 random chars, retry loop
- **Global Exception Handler** — no stack traces leak to clients

---

## 🏗 Architecture
