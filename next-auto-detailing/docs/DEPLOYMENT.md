# Deploy

## GitHub
Commit the repository, not `.env` files, credentials, customer records or database dumps. Review staged files before pushing.

## Render
Create PostgreSQL and a Python web service. Root directory `backend`; build `pip install -r requirements.txt`; start `gunicorn wsgi:app --workers 2 --threads 4 --timeout 90`; health check `/health`. Set `DATABASE_URL`, long random `SECRET_KEY`, exact `FRONTEND_ORIGIN`, and `COOKIE_SECURE=true`. Provision the owner through a private shell process; do not commit credentials.

## Vercel
Import repo; root `frontend`; build `npm run build`; output `dist`; environment `VITE_API_BASE_URL=https://your-render-service.onrender.com/api`. Alternatively use root `vercel.json` and verify project settings.

## HTTPS and SEO
Vercel/Render managed domains provide TLS; configure custom domain DNS and verify certificates. Use canonical domain, metadata, sitemap and robots policy before launch. Do not index private portal pages or account data.

## Email
Email verification and password recovery require provider credentials and implementation of hashed, expiring, single-use tokens before production.
