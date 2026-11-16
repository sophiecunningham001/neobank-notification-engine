# Neon Bank React demo app

This standalone Vite + React app is a responsive member-banking interface for a fictional credit union. It includes an overview dashboard, checking and savings balances, recent activity, card controls, account-to-account transfers, and settings views.

## Run locally

```bash
cd neobank-app
npm install
npm run dev
```

Create a production build with `npm run build`.

## Demo boundaries

All account data and actions are synthetic and held in local React state. Transfers only adjust sample balances in the current browser session; they do not call a bank, API, payment rail, card processor, or persist financial data. This is a UI prototype, not a financial product. Do not enter real credentials, payment-card information, or customer data.
