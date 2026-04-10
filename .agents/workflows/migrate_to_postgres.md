---
description: Migrate Django project to PostgreSQL
---

## Why migrate?
- **Scalability** – PostgreSQL handles larger datasets and concurrent connections better than SQLite.
- **Production‑ready** – Most cloud hosts (Render, Railway, Fly.io) provide managed PostgreSQL instances.
- **Feature set** – Advanced indexing, full‑text search, JSON fields, transactions, etc.

## What changes when you switch?
1. **Database engine** – Django will no longer create a local `db.sqlite3` file. Instead it connects to a remote PostgreSQL server.
2. **Tables** – Django **does not copy** existing SQLite tables automatically. You must run migrations (or import data) so that the same schema is created in Postgres.
3. **Data** – Existing data must be exported from SQLite and imported into PostgreSQL, or you can start with a fresh empty DB if you don’t need the old data.

---
## Step‑by‑step migration guide

### 1️⃣ Install PostgreSQL driver
```bash
pip install psycopg2-binary
```
Add it to `requirements.txt` (run `pip freeze > requirements.txt`).

### 2️⃣ Add a PostgreSQL config to `settings.py`
```python
import os
import dj_database_url

# Default – keep SQLite for local dev if DATABASE_URL not set
DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3"),
        conn_max_age=600,
    )
}
```
> **Note**: `dj-database-url` makes it easy to switch via the `DATABASE_URL` env var. Install it if you haven’t:
```bash
pip install dj-database-url
```

### 3️⃣ Create a PostgreSQL instance
- **Locally**: Install PostgreSQL via your OS package manager (e.g., `choco install postgresql` on Windows) and create a DB:
```sql
CREATE DATABASE manager_django;
CREATE USER manager_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE manager_django TO manager_user;
```
- **Render / Cloud**: When you create the web service, Render will provision a free PostgreSQL DB and give you a `DATABASE_URL` like:
```
postgres://manager_user:password@aws-us-east-1-portal.0.dblayer.com:5432/manager_django
```
Add that URL to the Render **Environment Variables**.

### 4️⃣ Apply migrations to create tables in Postgres
```bash
# Ensure DATABASE_URL points to the new Postgres DB
# (Render does this automatically; locally you can export it)
export DATABASE_URL=postgres://manager_user:password@localhost:5432/manager_django

python manage.py migrate
```
All tables defined in your `models.py` will be created.

### 5️⃣ (Optional) Migrate existing data from SQLite → PostgreSQL
If you have data you need to keep:
```bash
# 1. Dump data from SQLite
python manage.py dumpdata --natural-primary --natural-foreign --exclude auth.permission --exclude contenttypes > data.json

# 2. Switch DATABASE_URL to point to Postgres (as above)
export DATABASE_URL=postgres://manager_user:password@localhost:5432/manager_django

# 3. Load data into Postgres
python manage.py loaddata data.json
```
> **Tip**: For large datasets, tools like `pgloader` or `django‑postgres‑copy` are faster.

### 6️⃣ Verify the migration
- Run the development server: `python manage.py runserver` and check the admin panel – you should see the same records.
- Run any custom management commands or tests to ensure queries work.

### 7️⃣ Update deployment configuration (Render example)
1. In Render **Environment**, set:
   - `DATABASE_URL` – the URL Render gave you.
   - `DJANGO_SECRET_KEY` – keep your secret key safe.
2. Ensure `psycopg2-binary` and `dj-database-url` are in `requirements.txt`.
3. Redeploy the service – Render will run `python manage.py migrate` automatically if you add it to the **Build Command** or a **post‑deploy hook**.

---
## Common pitfalls & how to avoid them
| Symptom | Cause | Fix |
|----------|-------|-----|
| `no such table: core_resident` | Migrations not run on the new DB | Run `python manage.py migrate` after pointing `DATABASE_URL` to Postgres |
| `psycopg2.OperationalError: FATAL: password authentication failed` | Wrong credentials in `DATABASE_URL` | Double‑check username/password and that the DB user has access to the DB |
| `django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty.` | Missing `DJANGO_SECRET_KEY` env var on Render | Add it in the Render **Environment** section |
| Data missing after `loaddata` | Dumped JSON contains auth permissions that conflict | Exclude `auth.permission` and `contenttypes` when dumping (see command above) |

---
## Quick checklist (run before you push to production)
- [ ] `psycopg2-binary` and `dj-database-url` in `requirements.txt`
- [ ] `DATABASE_URL` env var set on your host (Render, Railway, etc.)
- [ ] `python manage.py migrate` runs without errors
- [ ] (If needed) `python manage.py loaddata data.json` completed successfully
- [ ] Verify admin UI and any API endpoints return expected data
- [ ] Commit and push changes (`settings.py` modifications, `requirements.txt`)

---
**You now have a complete, reproducible process to switch your Django project from SQLite to PostgreSQL and keep all tables (and optionally data) intact.**

Feel free to ask for any of the individual commands to be executed automatically (the workflow marks them with `// turbo` where appropriate), or let me know if you’d like a tailored version for a different cloud provider.
