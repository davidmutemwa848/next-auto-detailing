# Next Auto Detailing Professional

Vite frontend + Flask/PostgreSQL API. This is an initial implementation foundation, not a completed production release. Review `docs/LAUNCH_CHECKLIST.md` and `docs/SECURITY.md` before production. The supplied video has been transcoded for browser playback; the rest of the approved gallery media and complete business workflows still require implementation and verification. Never commit secrets or customer data.

## Local setup
Backend: `cd backend`, create a venv, `pip install -r requirements.txt`, configure `.env`, then `flask --app app:create_app init-db` and `flask --app app:create_app run`.
Frontend: `cd frontend`, `npm install`, set `VITE_API_BASE_URL`, then `npm run dev`.
See `docs/DEPLOYMENT.md` and `docs/SECURITY.md`.
