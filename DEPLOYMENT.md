# Deployment Guide

## Stack
- Frontend → Vercel
- Backend → Render (Docker)
- Database → Railway MySQL

---

## 1. Railway MySQL

1. Create a new MySQL service on Railway.
2. Copy the connection string — it looks like:
   `mysql://user:pass@host:port/dbname`
3. Convert it to JDBC format for Render:
   `jdbc:mysql://host:port/dbname?useSSL=true&serverTimezone=UTC&allowPublicKeyRetrieval=true`
4. Run `database/init.sql` via Railway's query console (or run each file in order).

---

## 2. Render (Backend)

Create a new Web Service → "Deploy from GitHub" → select this repo → Docker.

Set these environment variables in Render dashboard:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `jdbc:mysql://host:port/dbname?useSSL=true&serverTimezone=UTC&allowPublicKeyRetrieval=true` |
| `DB_USERNAME` | Railway MySQL username |
| `DB_PASSWORD` | Railway MySQL password |
| `JWT_SECRET` | Any long random string (32+ chars) |
| `EMAIL_USER` | Your Gmail address |
| `EMAIL_PASS` | Gmail App Password (not your login password) |
| `CORS_ALLOWED_ORIGINS` | `https://your-app.vercel.app` |
| `LOG_LEVEL` | `INFO` |

Health check path: `/actuator/health`

---

## 3. Vercel (Frontend)

1. Import the repo, set root directory to `frontend`.
2. Build command: `npm run build` (already has `CI=false`).
3. Output directory: `build`.

Set this environment variable in Vercel dashboard:

| Key | Value |
|-----|-------|
| `REACT_APP_API_URL` | `https://your-backend.onrender.com/api` |

---

## Gmail App Password Setup

1. Enable 2FA on your Google account.
2. Go to Google Account → Security → App Passwords.
3. Generate a password for "Mail" → use that as `EMAIL_PASS`.

---

## Deployment Order

1. Deploy Railway MySQL → get connection string
2. Deploy Render backend → set all env vars → wait for health check to pass
3. Deploy Vercel frontend → set `REACT_APP_API_URL` to Render URL
