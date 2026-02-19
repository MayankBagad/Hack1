# College Hackathon Management System

## Quick Start (MVP API)

### Prerequisites
- Python 3.11+

### Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]
```

### Run API
```bash
uvicorn app.main:app --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.

### Run tests
```bash
pytest -q
```

---

## Deploy on Vercel (API)

1. Push this repo to GitHub.
2. In Vercel, import the repository as a new project.
3. Ensure `vercel.json` and `api/index.py` are present (already included in this repo).
4. In Vercel Project Settings → Environment Variables, set:
   - `DATABASE_URL` to a managed Postgres URL for persistent data.
5. Deploy and test:
   - `https://<your-domain>/health`
   - `https://<your-domain>/docs`

### Notes
- Local dev defaults to SQLite (`sqlite:///./hackathon.db`) if `DATABASE_URL` is not set.
- On Vercel without `DATABASE_URL`, the app falls back to `/tmp/hackathon.db` to avoid read-only filesystem crashes.
- For stable live testing, set `DATABASE_URL` to managed Postgres (recommended).
- `postgres://...` and `postgresql://...` URLs are auto-normalized to `postgresql+psycopg://...`.

### Troubleshooting Vercel 500 (Function Crashed)
- Open `/health` and check `db_ready` and `startup_error` fields.
- If `db_ready` is `false`, configure `DATABASE_URL` to managed Postgres in Vercel env vars.
- Redeploy after changing env vars.

---

An end-to-end, college-specific platform to run hackathons from registration to final evaluation with strong verification, QR-based access, and digital audit trails.

## 1) Goals

- Eliminate manual paperwork and ID checks.
- Prevent fake registrations, duplicate entries, and food coupon misuse.
- Digitize and standardize shortlisting and final judging.
- Give organizers real-time dashboards, analytics, and exportable reports.

---

## 2) Core Modules

### A. Identity & Verification

**Student onboarding flow**
1. Student signs up with email + phone.
2. OTP verification for both channels.
3. Student uploads:
   - College ID card image
   - Masked Aadhaar details (store tokenized/hashed references, not raw sensitive data)
   - Live selfie
4. Face match service compares ID-card face vs selfie.
5. Admin verifies and approves/rejects with reasons.

**Security controls**
- Store files in private object storage.
- Encrypt sensitive PII at rest.
- Role-based access (Admin / Judge / Scanner / Student).
- Full audit log of verification actions.

### B. Hackathon Setup & Registration

- College admin creates event with rounds, dates, deadlines, venue, meal windows.
- Admin uploads problem statements.
- Students register as individual/team.
- Team captain submits round-1 PPT before deadline.
- Submission lock triggers automatically at deadline.

### C. Round-1 Evaluation (PPT Shortlisting)

- Configurable evaluation matrix and weights.
- Example criteria:
  - Innovation
  - Feasibility
  - Technical depth
  - Presentation clarity
  - Social impact
- Faculty/judges score inside dashboard.
- Auto-calculated weighted score + leaderboard.
- Shortlist action notifies teams via email/SMS/in-app.

### D. QR Entry Management

- Each verified participant gets event-entry QR.
- QR payload is signed, expiring, and non-forgeable.
- Gate scanner app validates signature + status.
- Real-time attendance logs.
- Duplicate-entry prevention (idempotent scan checks).

### E. QR Food Distribution

- Generate one-time meal QRs per participant:
  - Breakfast
  - Lunch
  - Dinner
- Time-window restrictions per meal.
- Food counter scanner marks token as consumed once.
- Real-time usage dashboard and exception handling.

### F. Final Round Submission & Judging

- Teams upload final PPT, GitHub link, optional demo video.
- Submission lock before live demos.
- Judges dashboard shows artifacts + scoring form.
- Real-time ranking, tie-break rules, and final result export.

### G. Admin Analytics & Reporting

- Verification stats (approved/pending/rejected)
- Attendance by time and gate
- Meal distribution counts and anomalies
- Round-wise score reports
- Certificate generation with QR verification links
- Event summary PDF/CSV export

---

## 3) Suggested Tech Architecture

## Web/App
- **Frontend**: React / Next.js (web), optional Flutter/React Native scanner app
- **Backend**: Node.js (NestJS/Express) or Django/FastAPI
- **Database**: PostgreSQL
- **Cache/Queue**: Redis + BullMQ/Celery
- **Storage**: S3-compatible object storage
- **Auth**: JWT + refresh tokens + optional SSO
- **Notifications**: Email + SMS provider integration
- **Face Match**: Pluggable provider/API

## Services
- Auth & user service
- Verification service
- Event/registration service
- Submission service
- Evaluation service
- QR token service
- Scan ingestion service
- Reporting service

## Deployment
- Dockerized microservices or modular monolith
- Nginx/API gateway
- CI/CD with automated tests
- Centralized logs + monitoring (ELK/Grafana)

---

## 4) Data Model (High-Level)

### Main entities
- `users` (student/admin/judge/scanner)
- `student_profiles` (college info, verification status)
- `verification_documents` (ID card, selfie, aadhaar metadata)
- `hackathons`
- `problem_statements`
- `teams` and `team_members`
- `submissions` (round1/final)
- `evaluation_criteria`
- `scores`
- `qr_tokens` (entry/meal tokens)
- `scan_logs`
- `notifications`
- `certificates`
- `audit_logs`

### Recommended status enums
- Verification: `PENDING`, `APPROVED`, `REJECTED`
- Submission: `DRAFT`, `SUBMITTED`, `LOCKED`
- QR token: `ACTIVE`, `CONSUMED`, `EXPIRED`, `REVOKED`

---

## 5) QR Design (Security-First)

**Token contents** (minimal and signed)
- token_id (UUID)
- participant_id
- hackathon_id
- purpose (`ENTRY`, `BREAKFAST`, `LUNCH`, `DINNER`)
- valid_from / valid_to
- nonce

**Rules**
- Sign tokens (JWS/HMAC), avoid exposing sensitive data.
- Validate signature, expiry, purpose, participant state, and prior use.
- Enforce one-time use for meal QRs.
- Allow one successful entry scan, then mark as already entered.
- Keep offline fallback queue for poor network; sync with conflict checks.

---

## 6) Evaluation Engine

### Weighted score formula

```text
total_score = Σ (criterion_score × criterion_weight)
```

### Tie resolution (example)
1. Higher score in `Technical depth`
2. Higher score in `Feasibility`
3. Lower standard deviation across judges (consensus preference)
4. Earliest submission timestamp

---

## 7) APIs (Illustrative)

### Verification
- `POST /auth/register`
- `POST /auth/verify-otp`
- `POST /verification/upload-documents`
- `POST /verification/face-match`
- `PATCH /admin/verification/:studentId`

### Event & submissions
- `POST /admin/hackathons`
- `POST /teams`
- `POST /submissions/round1`
- `POST /submissions/final`
- `POST /admin/submissions/lock`

### Evaluation
- `POST /admin/evaluation-matrix`
- `POST /judge/scores`
- `GET /admin/leaderboard?round=1`
- `POST /admin/shortlist`

### QR & scanning
- `POST /qr/generate/entry`
- `POST /qr/generate/meals`
- `POST /scan/entry`
- `POST /scan/meal`
- `GET /admin/scan-analytics`

---

## 8) Role-Based Access

- **Student**: register, submit PPT/final files, view QR, track status.
- **Admin**: verify students, configure events, shortlist, analytics, certificates.
- **Judge**: view assigned teams and submit scores.
- **Scanner**: scan entry/meal QR and view scan status only.

---

## 9) Compliance & Privacy

- Collect minimum data required.
- Mask Aadhaar data and store securely.
- Strict retention policy for sensitive artifacts.
- Consent capture at signup.
- Audit logs for all admin/judge actions.

---

## 10) MVP Delivery Plan

### Phase 1 (Core)
- Auth + OTP
- Student verification workflow
- Event setup + round-1 submission
- Round-1 evaluation + shortlist

### Phase 2 (On-ground digitization)
- Entry QR generation + scanner app
- Meal QR issuance + one-time redemption
- Attendance and meal dashboards

### Phase 3 (Finale & automation)
- Final submission lock + live judging
- Result exports + certificate generation
- AI assist (optional): PPT insights/plagiarism signals

---

## 11) Success Metrics

- 90%+ reduction in manual verification time.
- Zero duplicate meal redemption.
- <2 seconds average scan response at gates/counters.
- 100% evaluation traceability (who scored what and when).
- Complete event report generation in <5 minutes.

---

## 12) Future Enhancements

- Face recognition at gate as secondary factor.
- AI-assisted PPT rubric suggestions.
- GitHub plagiarism/similarity checks.
- Sponsor booth engagement tracking.
- Low-bandwidth progressive web mode for campus Wi-Fi congestion.
