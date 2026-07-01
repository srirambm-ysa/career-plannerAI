# Career AI Exposure Planner

## Project Overview
A 4-Step Wizard web app for **HR Managers** to evaluate employee exposure to AI/Automation, using task-level risk analysis powered by LLM (OpenRouter) and generating personalized upskilling roadmaps for each candidate.

The same job role differs vastly across industries — e.g., a Senior Vice President in Healthcare has entirely different tasks than a similar role in IT. The LLM generates tasks specific to the combination of **Industry Vertical + Job Title**, ensuring relevant risk profiles.

## Tech Stack
- **Backend:** Python 3.13+, Flask 3.x
- **Frontend:** Jinja2 templates, Tailwind CSS (CDN), Vanilla JavaScript
- **Database:** SQLite + SQLAlchemy ORM
- **Auth:** Flask-Login + Werkzeug (email/password) + Flask-Dance (Google OAuth)
- **AI:** OpenRouter API via OpenAI Python SDK
- **Salary Data:** Adzuna API (free tier) for live job posting salary benchmarks, LLM fallback for uncovered countries
- **PDF:** Browser print-to-PDF (styled HTML preview page with `@media print` CSS)
- **Deployment:** Render free tier

## Core Features
1. User registration & login — Email/password OR Google OAuth
2. **4-Step Wizard (HR Manager screens a candidate):**
   - **Step 1: Industry & Country Selection** — HR Manager picks the candidate's industry from a pre-populated lookup list and selects the candidate's country for salary benchmarking. Industry value is **consistent** across all candidates screened by the same HR Manager (pre-filled after first use). Country defaults to previously used value.
   - **Step 2: Profile Input** — HR Manager enters job title and years of experience, then adds all relevant tasks for the candidate's role. An **Add task** command creates empty placeholders for task descriptions. A **Suggested Tasks** button triggers an LLM call to generate 12 suggested tasks relevant to the specific industry + job title. Each suggestion has a checkbox; on check, the task description fills the corresponding empty placeholder. Task selection progresses in this additive manner.
   - **Step 3: AI Scores** — AI scores each selected task for AI exposure (1-10). Results shown as color-coded risk cards. The "Generate Roadmap" button triggers roadmap creation and redirects to the Summary Page.
   - **Summary Page (post-generation)** — Confirmation page shown after roadmap generation. Includes:
     - Overall risk score badge
     - Salary benchmark for the role (Adzuna API or LLM fallback)
     - Condensed roadmap preview (top 3-5 items)
     - Links to Dashboard and detailed report
   - **Detailed Report** — Full assessment detail page accessible from Dashboard. Includes:
     - Complete task breakdown with risk scores
     - Salary benchmark with source and confidence
     - Full roadmap with all items
     - Notes field
     - PDF export button
 3. **Dashboard** — Completed assessment history with:
    - **Search/Filter** by Industry Vertical and Job Title
    - **Delete** button to remove unwanted assessments
 4. **PDF export** — Browser-based print-to-PDF from the detailed report page. Clean A4 formatting with `@media print` CSS rules. No server-side PDF library required.

## Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Landing page |
| GET/POST | `/register` | Register (email/password) |
| GET/POST | `/login` | Login (email/password or Google OAuth) |
| GET | `/logout` | Logout |
| GET | `/assessment/` | Start wizard (redirects to step 1) |
| GET/POST | `/assessment/step/1` | Industry selection |
| GET/POST | `/assessment/step/2` | Profile & tasks |
| POST | `/assessment/step/2/suggest-tasks` | AI task suggestions |
| GET/POST | `/assessment/step/3` | Risk results → generate roadmap |
| GET | `/assessment/summary/<id>` | Summary page (post-generation confirmation with risk, salary, condensed roadmap) |
| GET | `/assessment/<id>` | Detailed report (full roadmap, scores, salary, notes, PDF) |
| GET | `/assessment/<id>/pdf` | Print-friendly HTML preview |
| GET | `/assessment/<id>/json` | Export assessment as JSON |
| POST | `/assessment/<id>/notes` | Save notes for assessment |
| POST | `/assessment/<id>/delete` | Delete assessment (with confirmation modal) |
| GET | `/dashboard` | Assessment history with search/filter, sort (newest/oldest/A-Z) |

## Data Model
```
User — id, email, password_hash (nullable for OAuth), name, avatar_url, last_industry, created_at
OAuthAccount — id, user_id, provider, provider_user_id, provider_email
Assessment — id, user_id, job_title, industry, years_exp, country, step (1-4), status (draft|completed), created_at, completed_at, salary_range, salary_source, salary_confidence
Task — id, assessment_id, description, risk_score, explanation, category
RoadmapItem — id, assessment_id, skill_name, priority, timeline (short|medium|long), description, category, resources (JSON)
```

## Enhancements Implemented
- **Error pages:** Custom 404 and 500 pages with branded styling
- **Password confirmation:** Additional field on register + backend validation
- **Remember me:** Checkbox on login using Flask-Login's `remember` parameter
- **Flash auto-dismiss:** Messages fade out after 4 seconds
- **Delete confirmation:** Custom modal replacing browser `confirm()` dialog
- **Sort options:** Dashboard sort by newest, oldest, or industry A-Z
- **Relative time:** Assessment age shown as "2d ago", "3mo ago", etc.
- **Mobile responsive:** Dashboard wraps in `overflow-x-auto` for small screens
- **Clear all tasks:** Button to remove all task placeholders on step 2
- **Keyboard shortcuts:** Escape key closes the suggestion modal
- **Risk score tooltip:** Info icon explaining 1-10 risk scale
- **Confetti:** Celebration animation on roadmap completion page
- **JSON export:** `/assessment/<id>/json` endpoint for raw data download
- **Notes field:** Per-assessment textarea, saved via POST `/assessment/<id>/notes`
- **Page titles:** Step numbers in `<title>` tags (e.g. "Step 2 of 4")

## Enhancements Planned
- **Country selection:** Step 1 gets a country dropdown alongside industry
- **Summary Page:** Post-generation confirmation with overall risk score, salary benchmark, condensed roadmap preview
- **Detailed Report page:** New page accessible from Dashboard with full scores, salary, roadmap, notes, and PDF export
- **Salary benchmark:** Adzuna API (free tier) fetches live salary ranges by job title + country; LLM fallback for unsupported countries. Shown on both Summary Page and Detailed Report
- **Adzuna credentials:** `ADZUNA_APP_ID` and `ADZUNA_API_KEY` added to env vars

## Known Quirks
- LLM responses are matched to tasks by index (not description string) to avoid mismatches from minor rephrasing.
- Empty task categories display as `—` in the print preview.
- Abandoned draft assessments are auto-cleaned when starting a new wizard session.
