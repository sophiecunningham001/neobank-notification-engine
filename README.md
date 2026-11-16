# Neon Bank Credit Union Sandbox

This project is a lightweight, production-styled banking sandbox built in FastAPI.
It includes a seeded demo customer, synthetic account data, cards, transfer logic,
ledger tracking, fraud posture, audit events, and a dashboard UI.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:
- http://localhost:8000/
- http://localhost:8000/docs

## Demo login

- Email: `sandbox@example.test`
- Password: `ChangeMe123!`

## Included features

- JWT authentication
- account and card endpoints
- payment authorization scenarios
- transfer workflow
- ledger and GL balances
- fraud posture and alerts
- audit event feed
- static banking dashboard UI

## Notes

This is synthetic, sandbox-only data. It is not connected to any live bank or network.
