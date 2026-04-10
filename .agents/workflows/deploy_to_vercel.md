---
description: Deploy Django site to Vercel (serverless) and configure Android APK base URL
---

## Overview
Vercel is optimized for **serverless functions**. To run a full‑stack Django app you can expose the WSGI application through a Python serverless function. This workflow shows how to:
1. Prepare the Django project for a serverless environment.
2. Add the required Vercel configuration files.
3. Deploy to Vercel via the Vercel CLI (or GitHub integration).
4. Update the Android APK to point at the live Vercel URL.

> **Important:** Vercel serverless functions have a **maximum execution time of 60 seconds** and a **cold‑start latency**. For a typical CRUD API this works fine, but long‑running tasks (e.g., large PDF generation) should be off‑loaded to a background worker or external service.

---
## Prerequisites
- Node.js (>= 18) and npm installed.
- Vercel CLI (`npm i -g vercel`).
- Git repository for the Django project (GitHub, GitLab, or Bitbucket).
- PostgreSQL database (Render, Railway, Supabase, or any managed service). Vercel does not host relational DBs.
- Android source code where the API base URL is defined.

---
## 1️⃣ Prepare Django for production
### a) Install required packages
```bash
pip install gunicorn dj-database-url psycopg2-binary whitenoise
pip freeze > requirements.txt   # // turbo – generate requirements file
```
### b) Settings adjustments (`manager_django/settings.py`)
```python
import os, dj_database_url

# SECURITY
DEBUG = False
ALLOWED_HOSTS = ["*.vercel.app", "yourcustomdomain.com"]

# DATABASE – use DATABASE_URL env var (Vercel will expose it)
DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3"),
        conn_max_age=600,
    )
}

# STATIC FILES – serve via WhiteNoise (required for serverless)
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
```
### c) Create a **WSGI entry point** (already exists as `manager_django/wsgi.py`). No changes needed.

---
## 2️⃣ Add Vercel configuration files
### a) `vercel.json` (project root)
```json
{
  "version": 2,
  "builds": [
    { "src": "api/**/*.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "/api/django.py" }
  ]
}
```
> This tells Vercel to route **all** incoming requests to the Python serverless function `api/django.py`.

### b) Serverless function – `api/django.py`
```python
import os
import sys
from pathlib import Path

# Add the Django project to PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

# Set DJANGO_SETTINGS_MODULE before importing Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manager_django.settings')

# Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel expects a callable named `handler`
def handler(event, context):
    # Vercel's python builder provides a `vercel_wsgi` helper
    from vercel_wsgi import run_wsgi
    return run_wsgi(application, event, context)
```
> **Note:** `vercel_wsgi` is part of the `@vercel/python` runtime. No extra install needed.

### c) (Optional) Static files handling
If you want Vercel to serve static assets directly, add a `static/` folder and copy the collected static files there during the build step.
Create a **build script** in `package.json`:
```json
"scripts": {
  "build": "python manage.py collectstatic --noinput && cp -r staticfiles/* static/"
}
```
Vercel will run `npm run build` before deploying.

---
## 3️⃣ Deploy to Vercel
### a) Initialize Vercel in the repo (run once)
```bash
vercel login                     # // turbo – opens a browser for auth
vercel link                      # // turbo – links the local folder to a Vercel project
```
### b) Set environment variables (via Vercel dashboard or CLI)
```bash
vercel env add DATABASE_URL production
vercel env add DJANGO_SECRET_KEY production
# Add any other secrets (e.g., PAYTM_MERCHANT_ID)
```
### c) Deploy
```bash
vercel --prod   # // turbo – deploys the current commit to production
```
Vercel will build the Python function, install `requirements.txt`, run the `build` script, and expose the site at `https://<project-name>.vercel.app`.

---
## 4️⃣ Verify the deployment
1. Open the URL in a browser – you should see your Django site (admin, API endpoints, etc.).
2. Test an API call (e.g., `https://<project>.vercel.app/api/resident/`) – ensure JSON response works.
3. Check the Vercel logs (Dashboard → Functions → Logs) for any import errors.

---
## 5️⃣ Update Android APK base URL
Locate the constant that stores the API URL (often in `Constants.java` or a Kotlin `object`). Replace the localhost URL with the Vercel URL:
```java
public static final String BASE_URL = "https://<project-name>.vercel.app/";
```
Re‑build the APK:
```bash
./gradlew assembleRelease   # // turbo – builds the release APK
```
Distribute the new APK to testers or upload to the Play Store.

---
## 6️⃣ Post‑deployment checklist
- [ ] **Database connectivity** – confirm the `DATABASE_URL` points to a live PostgreSQL instance.
- [ ] **Static files** – verify CSS/JS/images load (they are served from `/static/`).
- [ ] **CORS** – if the Android app makes cross‑origin requests, add `django-cors-headers` and set `CORS_ALLOWED_ORIGINS` to `https://<project>.vercel.app`.
- [ ] **Timeouts** – ensure any view that might take > 50 s is refactored (e.g., move PDF generation to a background worker).
- [ ] **Security** – keep `DEBUG=False`, set a strong `DJANGO_SECRET_KEY`, and enable HTTPS (Vercel provides it automatically).

---
## 7️⃣ Common pitfalls & fixes
| Issue | Likely cause | Fix |
|-------|--------------|-----|
| `ImportError: No module named 'vercel_wsgi'` | Missing `@vercel/python` runtime version. | Ensure `vercel.json` uses `"@vercel/python"` and run `vercel --prod` again.
| 502 Bad Gateway | `STATIC_ROOT` not collected or missing files. | Run `python manage.py collectstatic` in the build script and copy files to `static/`.
| 504 Gateway Timeout | View takes > 60 s. | Off‑load heavy work to a Celery worker or external service.
| Database connection refused | `DATABASE_URL` not set or wrong credentials. | Add the env var in Vercel dashboard; test locally with `export DATABASE_URL=...`.

---
## 8️⃣ Quick command summary (turbo‑enabled)
```bash
# 1. Install Vercel CLI (once)
npm i -g vercel   # // turbo

# 2. Install Python deps & generate requirements.txt
pip install gunicorn dj-database-url psycopg2-binary whitenoise
pip freeze > requirements.txt   # // turbo

# 3. Login & link project
vercel login   # // turbo – opens browser
vercel link    # // turbo – creates/vercel.json if missing

# 4. Add env vars (run once per env)
vercel env add DATABASE_URL production
vercel env add DJANGO_SECRET_KEY production

# 5. Deploy
vercel --prod   # // turbo – deploys to Vercel

# 6. Build Android APK
./gradlew assembleRelease   # // turbo – creates new APK
```
---
**You now have a complete, reproducible workflow to host your Django backend on Vercel and point your Android APK at the live endpoint.**

Feel free to ask me to run any of the `// turbo` commands, open the workflow file, or clarify any step.
