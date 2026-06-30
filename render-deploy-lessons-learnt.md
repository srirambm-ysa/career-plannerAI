# Render Deployment — Steps & Lessons Learnt

## Overview
Deploying a Flask + PostgreSQL app (Career Planner) to Render's free tier with CI/CD via GitHub.

---

## Steps

### 1. Database — Neon PostgreSQL
- Created a free PostgreSQL database at https://console.neon.tech
- Copied the connection string:
  ```
  postgresql://user:password@ep-xxx.aws.neon.tech/neondb?sslmode=require
  ```
- Set as `DATABASE_URL` in `.env` and later in Render's env vars

### 2. Git Init & GitHub Push
- Initialized git: `git init`
- Created `.gitignore` (exclude `.env`, `instance/`, `__pycache__/`, `*.db`)
- Committed source code: `git add . && git commit -m "Initial commit"`
- Created repo on GitHub: `srirambm-ysa/career-plannerAI`
- Pushed via Personal Access Token (classic, scope: `repo`)

### 3. render.yaml
- Created `render.yaml` for Blueprint-based deployment (infrastructure as code)
- Defines: Python env, build command (`pip install -r requirements.txt`), start command (`gunicorn run:app`), free plan
- All 8 env vars listed with `sync: false` (values entered in Render dashboard, not in repo)

### 4. Render Blueprint Deployment
- Dashboard → New → Blueprint → connect GitHub repo
- Render auto-reads `render.yaml`, prompts for env var values
- Filled from `.env` (with `OAUTHLIB_INSECURE_TRANSPORT=0` for production)
- Applied — Render builds and deploys

### 5. Google OAuth Redirect URI
- Render URL: `https://career-planner-q1mq.onrender.com`
- Added to Google Cloud Console:
  ```
  https://career-planner-q1mq.onrender.com/login/google/authorized
  ```

### 6. CI/CD
- Every `git push` to `master` triggers auto-redeploy
- No manual rebuild needed after initial setup

---

## Issues Faced & Resolved

### Issue 1: WeasyPrint GTK dependency on Windows
- **Problem:** WeasyPrint requires GTK system libraries which don't exist on Windows
- **Fix:** Switched to browser print-to-PDF via HTML preview with `@media print` CSS

### Issue 2: AI scoring — description mismatch
- **Problem:** LLM rephrases task descriptions, so string matching between generated tasks and scored tasks failed
- **Fix:** Changed from description-based matching to index-based matching (nth task returned by LLM)

### Issue 3: Empty draft assessments on dashboard
- **Problem:** Abandoned wizard sessions created draft assessments cluttering the dashboard
- **Fix:** Dashboard filter: `status='completed'` only; auto-delete drafts on new wizard session

### Issue 4: PDF formatting
- **Problem:** Roadmap item descriptions overflowing, empty categories showing awkwardly, OpenRouter branding visible
- **Fix:** Added `word-break: break-word`, `—` fallback for empty categories, removed OpenRouter footer

### Issue 5: PostgreSQL vs SQLite schema compatibility
- **Problem:** `ALTER TABLE` auto-migration syntax differs between SQLite and PostgreSQL
- **Fix:** Used `ALTER TABLE assessments ADD COLUMN notes TEXT` — both engines support this syntax identically

### Issue 6: Git push authentication (Windows CLI)
- **Problem:** `git push` failed with "could not read Username" — no interactive prompt in non-TTY environments
- **Fix:** Created a Personal Access Token (classic) on GitHub, used `git credential.helper store` to persist it

### Issue 7: Render free tier cold start
- **Problem:** Free Render web service sleeps after 15 min idle
- **Effect:** First request after idle takes ~30 seconds (database connection + app boot)
- **Acceptance:** Acceptable for a free-tier hobby project

### Issue 8: Google OAuth redirect mismatch
- **Problem:** "Access blocked: This app's request is invalid" on Google login
- **Cause:** Render URL unknown until deployment — redirect URI not yet added to Google Cloud Console
- **Fix:** After deployment, added the exact Render URL to Google OAuth authorized redirect URIs

---

## File Structure (relevant to deployment)

| File | Purpose |
|------|---------|
| `render.yaml` | Render Blueprint config (infra as code) |
| `.env.example` | Template for environment variables (no secrets) |
| `.env` | Local env vars (gitignored, never committed) |
| `.gitignore` | Excludes secrets, cache, DB files from git |
| `requirements.txt` | Python dependencies (includes `gunicorn`, `psycopg2-binary`) |
| `Procfile` | Render start command (`gunicorn run:app`) |
| `how-to-deploy-on-render.md` | Deployment instructions |

---

## Commands Quick Reference

```bash
# Local dev (SQLite)
python run.py

# Deploy to Render
git add .
git commit -m "description"
git push

# Render auto-deploys master branch
```

## Env Vars Required on Render

| Variable | Notes |
|----------|-------|
| `SECRET_KEY` | Flask secret, generate a random one |
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` |
| `GOOGLE_OAUTH_CLIENT_ID` | From Google Cloud Console |
| `GOOGLE_OAUTH_CLIENT_SECRET` | From Google Cloud Console |
| `OAUTHLIB_INSECURE_TRANSPORT` | `0` (production), `1` (local dev) |
