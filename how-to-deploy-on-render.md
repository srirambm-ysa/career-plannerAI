# Deploy Career Planner on Render (Free)

## Prerequisites

- **GitHub account** with the code pushed to a repository
- **Neon PostgreSQL** database already created and working
- **Google OAuth** credentials configured
- **OpenRouter API key**

## Step 1: Deploy via Blueprint (render.yaml)

1. Go to https://dashboard.render.com
2. Click **New** → **Blueprint**
3. Connect your GitHub account
4. Select the `career-plannerAI` repository
5. Render reads `render.yaml` and shows the configuration

## Step 2: Fill Environment Variables

You'll be prompted to enter values for these (paste from your `.env` file):

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Your Flask secret key |
| `DATABASE_URL` | Your Neon PostgreSQL connection string |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` |
| `GOOGLE_OAUTH_CLIENT_ID` | Your Google OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Your Google OAuth client secret |
| `OAUTHLIB_INSECURE_TRANSPORT` | `0` |

## Step 3: Deploy

Click **Apply**. Render will:
- Build the app (`pip install -r requirements.txt`)
- Start the web service (`gunicorn run:app`)
- Assign a URL like `https://career-planner.onrender.com`

## Step 4: Update Google OAuth Redirect URIs

1. Go to https://console.cloud.google.com/apis/credentials
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   https://career-planner.onrender.com/login/google/authorized
   ```
4. Save

## Step 5: Visit Your App

Open the Render URL in your browser. Register a new account and create an assessment.

## CI/CD

Every `git push` to `master` triggers an automatic redeploy on Render.

```bash
git add .
git commit -m "your changes"
git push
```

## Notes

- **Free tier sleep:** Render sleeps after 15 minutes of inactivity. First request after idle takes ~30 seconds to wake up.
- **Persistent data:** Lives in Neon PostgreSQL, not on Render's ephemeral disk.
- **Logs:** Available at Dashboard → your service → **Logs** tab.
- **Custom domain:** Render free tier supports custom domains — add a CNAME record pointing to `career-planner.onrender.com`.
