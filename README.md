# Payment Banking Sandbox v2

Expanded local FastAPI + PostgreSQL + Docker sandbox built from the supplied ZIP.

**Synthetic data only.** It is not connected to First PREMIER Bank, Visa, Mastercard, ACH, or any live financial network. The visible full PAN/account/routing values are deliberately synthetic test identifiers and must never be replaced with real customer data.

## Start

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

Seed login: `sandbox@example.test` / `ChangeMe123!`

## Included

- JWT authentication
- synthetic test checking account with complete test account/routing values
- synthetic test cards with complete test PANs
- card activation/deactivation
- payment authorization/decline/fraud/insufficient-funds scenarios
- idempotency keys
- PostgreSQL persistence
- double-entry-style ledger entries
- audit log
- payment history
- Docker health dependency
- OpenAPI documentation

## Test PANs

The PANs in the seed data are standard-looking test values and have no payment value. Do not substitute live PANs, CVVs, PINs, authentication codes, or bank credentials.

| PAN | Scenario |
|---|---|
| `4111111111111111` | Approved |
| `4000000000000002` | Declined (generic) |
| `4000000000009995` | Declined (insufficient funds) |
| `4000000000000259` | Blocked (fraud) + risk alert |

## API quick reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness probe |
| `/auth/login` | POST | JWT access token (`access_token`, `token_type: bearer`) |
| `/api/accounts` | GET | Accounts with full test account/routing numbers |
| `/api/cards` | GET | Cards with full test PANs |
| `/api/cards/{id}/activate` · `/deactivate` | POST | Card lifecycle |
| `/api/payments/authorize` | POST | Card authorization (scenario matrix above), idempotent via `idempotency_key` |
| `/api/payments/history` | GET | Authorization/payment history with status + merchant |
| `/api/transfers` | POST | Internal transfers (idempotent) |
| `/api/ledger/entries` · `/api/ledger/gl-accounts` | GET | Double-entry journal + trial balance |
| `/api/fraud/posture` · `/api/fraud/alerts` | GET | Risk posture and alerts |
| `/api/audit/events` | GET | Append-only audit feed |
| `/api/test/simulate-error` | POST | Simulated error envelope |

Authorize example:

```bash
TOKEN=$(curl -s localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"sandbox@example.test","password":"ChangeMe123!"}' | jq -r .data.access_token)

curl -s localhost:8000/api/payments/authorize \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"pan":"4111111111111111","amount_cents":2599,"merchant":"Test Coffee Co","idempotency_key":"order-123"}'
```

## Also inside (v1 banking SPA)

The same container serves the full banking UI at `/` — dashboard, transfers,
bill pay, ledger, fraud, audit, security center. Extra seeded customers:
`demo@meridian.bank` / `Meridian#2026` and `dadger041253@gmail.com`
(the SPA uses session + TOTP MFA; the v2 API surface uses plain JWT).

## Local development without Docker

```bash
pip install -r requirements.txt
cd backend
DB_BACKEND=sqlite EXPOSE_TOTP=1 python main.py   # embedded SQLite preview
```

## Layout

```
├── frontend/            # Static SPA served by FastAPI
├── backend/             # FastAPI app (auth, JWT, accounts, cards, payments,
│                        #  transfers, ledger, fraud, audit, errors)
├── database/            # schema.sql + seed.sql (PostgreSQL), *_sqlite.sql (preview)
├── verifier/            # acceptance criteria + self-check scripts + run log
├── docker-compose.yml   # app + postgres with health dependency
├── Dockerfile           # all-in-one image (embedded PostgreSQL)
├── .env.example
└── requirements.txt
```
