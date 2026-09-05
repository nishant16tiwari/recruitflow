# SUBMISSION

## Live links

| | |
|---|---|
| **Live app** | [recruitflow-pi.vercel.app](https://recruitflow-pi.vercel.app) |
| **Backend URL** | [recruitflow-api-dscf.onrender.com](https://recruitflow-api-dscf.onrender.com/) |
| **Source code** | [github.com/nishant16tiwari/recruitflow](https://github.com/nishant16tiwari/recruitflow) |

> **Cold start note**: the backend is on Render's free tier, which sleeps after 15 minutes of inactivity. The first request after a period of inactivity (including the first login when you open the live app) can take 30–60 seconds to respond. This is expected — wait and it will come through.

## Demo credentials

All passwords: `password123`

| Role | Email | Name |
|---|---|---|
| Recruiter | `Nishant@recruitflow.dev` | Nishant Tiwari |
| Recruiter | `Shivam@recruitflow.dev` | Shivam Singh |
| Interviewer | `Hardik.interviewer@recruitflow.dev` | Hardik Pandaya |
| Interviewer | `Rohit.interviewer@recruitflow.dev` | Rohit Sharma |
| Interviewer | `amara.interviewer@recruitflow.dev` | Amara |

Log in as a **Recruiter** to see the full pipeline: dashboard, applications, job openings, alerts, bulk actions, and CSV export. Log in as an **Interviewer** to see the restricted view: only applications assigned to that account, feedback submission, and "My Interviews."

## Running it locally instead

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # point DATABASE_URL at your local Postgres
alembic upgrade head
python seed.py
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env      # VITE_API_URL=http://localhost:8000
npm run dev
```

Full setup, architecture, and business-rule documentation: see `README.md` and `mdfiles/`.

## What to check first

1. Log in as `Nishant@recruitflow.dev` → Dashboard (real metrics, not hardcoded)
2. Applications → search/filter/sort, select a few, try a bulk advance — note the per-candidate success/failure results
3. Open any application → advance/reject/reinstate it, watch the pipeline stepper and timeline update
4. Log in as `Hardik.interviewer@recruitflow.dev` → confirm you only see applications assigned to that account, and that stage-change actions aren't available
5. Alerts page — dismiss one, and check back after it's had time to stall again
