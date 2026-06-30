# Deployment Options

## Option A: Render + Neon PostgreSQL (FREE)
**Cost: $0/mo | Complexity: Medium | Recommended**

| Service | Plan | Cost |
|---------|------|------|
| Render Web Service | Free (512 MB RAM, 0.1 CPU) | $0 |
| Neon PostgreSQL | Free (0.5 GB, auto-sleep) | $0 |

**Pros:** Fully hosted, custom domain, automatic HTTPS, git-based deploys
**Cons:** Free tier sleeps after 15 min idle (~30s wakeup), Neon free tier limited rows

**Setup:**
1. Push code to GitHub
2. Create Web Service on Render → connect repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn run:app`
5. Add environment variables (API keys, Google OAuth, SECRET_KEY)
6. Create Neon PostgreSQL → copy connection string → set as `DATABASE_URL`
7. Configure Google OAuth redirect URI to your Render URL

**Files needed:** `Procfile`, `requirements.txt` (add gunicorn + psycopg2-binary)

---

## Option B: PythonAnywhere (FREE)
**Cost: $0/mo | Complexity: Low | Easiest for beginners**

| Service | Plan | Cost |
|---------|------|------|
| PythonAnywhere Web | Free (1 web app, 512 MB storage) | $0 |
| PythonAnywhere MySQL | Free (included) | $0 |

**Pros:** Simplest setup, no sleep, built-in MySQL, file editor in browser
**Cons:** No custom domain (your-username.pythonanywhere.com), limited storage, no background tasks

**Setup:**
1. Upload files via web console or git
2. Create virtual environment, `pip install -r requirements.txt`
3. Configure WSGI file to import `run:app`
4. Set up MySQL database, update `DATABASE_URL`
5. Configure static files mapping in web tab
6. Set environment variables via web UI

**Files needed:** Manual WSGI config (no extra files)

---

## Option C: Render + Render PostgreSQL ($7/mo)
**Cost: $7/mo | Complexity: Low | Single provider**

| Service | Plan | Cost |
|---------|------|------|
| Render Web Service | Free (512 MB RAM) | $0 |
| Render PostgreSQL | Mini (1 GB storage) | $7/mo |

**Pros:** One provider, no external dependencies, easy PG admin dashboard
**Cons:** $7/mo for DB, same sleep issue on web service

**Setup:** Same as Option A, but create PostgreSQL on Render instead of Neon.

---

## Option D: Fly.io (FREE tier)
**Cost: $0/mo | Complexity: Medium-High**

| Service | Plan | Cost |
|---------|------|------|
| Fly.io VM | Free (3 shared VMs, 256 MB each) | $0 |
| Fly.io PostgreSQL | Free (1 GB, limited) | $0 |

**Pros:** No sleep, global regions, no cold starts
**Cons:** Needs Dockerfile, steeper learning curve

**Setup:** Requires `Dockerfile` and `fly.toml`.

---

## Files Required Setup

### For Option A or C (Render):
Create `Procfile` in project root:
```
web: gunicorn run:app
```

Add to `requirements.txt`:
```
gunicorn==23.0.0
psycopg2-binary==2.9.10
```

### For Option D (Fly.io):
Create `Dockerfile` in project root.

### Env Variables (all options):
| Variable | Where to get it |
|----------|----------------|
| `SECRET_KEY` | Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | From your PostgreSQL provider (Render/Neon/Fly) |
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` (default, works on free credits) |
| `GOOGLE_OAUTH_CLIENT_ID` | Google Cloud Console → APIs & Services → Credentials |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google Cloud Console → APIs & Services → Credentials |
| `OAUTHLIB_INSECURE_TRANSPORT` | Set to `0` in production (leave as `1` for dev) |

### Google OAuth Setup:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add Authorized redirect URIs:
   - `https://your-app.onrender.com/login/google/authorized` (Render)
   - `https://your-app.onrender.com/login/google` (alternative)
4. Copy Client ID and Secret to env variables

### Important Notes:
- **SQLite won't work on Render** — filesystem is ephemeral, data is lost on restart. Must use PostgreSQL.
- **Free Render sleep** — The free web service sleeps after 15 min idle. First request after sleep takes 30-60s. Upgrade to Starter ($7/mo) to disable sleep.
- **Neon free tier** — 0.5 GB storage, 100 hr compute/month, auto-sleeps after 5 min.
- **Google OAuth callbacks** — Must match exactly what's configured in Google Cloud Console.
