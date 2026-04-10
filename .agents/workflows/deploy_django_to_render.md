---
description: Deploy Django site to Render and configure APK
---

## Overview
This workflow guides you through publishing your Django application (located at `manager_django`) to **Render.com** (a free‑tier cloud platform) and updating your Android APK to communicate with the live backend.

### Prerequisites
- Git installed and a GitHub (or GitLab/Bitbucket) account.
- Render.com account (free tier works for small projects).
- Basic knowledge of Django settings, static files, and environment variables.
- Access to the Android project source (to change the API base URL).

## Steps

1. **Prepare Django for Production**
   ```
   # In manager_django/settings.py
   DEBUG = False
   ALLOWED_HOSTS = ["your-app.onrender.com", "yourcustomdomain.com"]
   
   # Add WhiteNoise for static files
   MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
   STATIC_ROOT = BASE_DIR / "staticfiles"
   ```
   // turbo (optional) – you may run a command to install WhiteNoise if not present.

2. **Create `requirements.txt`**
   ```bash
   pip freeze > requirements.txt
   ```
   // turbo – automatically generate the file.

3. **Add a `Procfile`** (Render uses this to start the app)
   ```
   web: gunicorn manager_django.wsgi:application --bind 0.0.0.0:$PORT
   ```
   // turbo – create file.

4. **Add a `runtime.txt`** (specify Python version)
   ```
   python-3.11.8
   ```
   // turbo – create file.

5. **Commit and Push to GitHub**
   ```bash
   git init   # if not already a repo
   git add .
   git commit -m "Prepare for Render deployment"
   git remote add origin https://github.com/yourusername/manager_django.git
   git push -u origin master
   ```
   // turbo – you may run these commands if the repo is ready.

6. **Create a Render Web Service**
   - Log in to Render.com.
   - Click **New** → **Web Service**.
   - Connect the GitHub repository you just pushed.
   - Set **Build Command** to `pip install -r requirements.txt`.
   - Set **Start Command** to the line from the Procfile (`gunicorn manager_django.wsgi:application`).
   - Choose **Free** plan (or a paid tier if you need a custom domain).
   - Add environment variables:
     - `DJANGO_SECRET_KEY` – your secret key.
     - `DATABASE_URL` – Render will create a PostgreSQL instance; copy the URL.
     - Any other custom settings (e.g., `PAYTM_MERCHANT_ID`).
   - Click **Create Web Service** and wait for the build to finish.

7. **Migrate Database on Render**
   After the service is live, open the **Shell** tab in Render and run:
   ```bash
   python manage.py migrate
   ```
   // turbo – optional command.

8. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```
   // turbo – optional command.

9. **Verify the Live Site**
   - Visit `https://your-app.onrender.com`.
   - Ensure all pages load and API endpoints (e.g., `/api/...`) return JSON.
   - Check CORS headers if your Android app makes cross‑origin requests (add `django-cors-headers` if needed).

10. **Update Android APK Base URL**
    - Open the Android project (likely in `android/app/src/main/java/...`).
    - Locate the constant that stores the API base URL (e.g., `BASE_URL = "http://127.0.0.1:8000/"`).
    - Replace it with the Render URL:
      ```java
      public static final String BASE_URL = "https://your-app.onrender.com/";
      ```
    - Re‑build the APK:
      ```bash
      ./gradlew assembleRelease
      ```
    - Distribute the new APK to testers or upload to the Play Store.

11. **Optional: Custom Domain & SSL**
    - In Render, go to **Custom Domains**, add your domain, and follow the DNS instructions.
    - Render automatically provisions a free SSL certificate.

12. **Post‑Deployment Checklist**
    - Test all payment flows (Razorpay/Paytm) in the live environment.
    - Verify email sending (if any) works with the production email backend.
    - Monitor logs on Render for any errors.

---
**End of Workflow**
