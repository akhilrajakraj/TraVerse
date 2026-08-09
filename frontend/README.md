# TraVerse Frontend

React + TypeScript + Vite frontend for the TraVerse monorepo.

## Chapter 1 verification

This foundation intentionally contains no feature UI. It proves the frontend can reach the existing Django platform health endpoint before application features are built.

### Requirements

- Node.js 20.19+
- TraVerse backend running on `http://localhost:8000`

### Setup

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run verify:api
npm run dev
```

The browser application runs on `http://localhost:5173`.

### Environment rule

Only browser-safe values may use the `VITE_` prefix. Never put API keys, database credentials, JWT signing secrets, or other private values in frontend environment variables.

### Backend contract verified

The current TraVerse backend exposes `/health/` at the project root. Its response is shaped as:

```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "django": "healthy"
  }
}
```

The frontend verification code deliberately validates this actual response shape rather than assuming the older chapter example.
