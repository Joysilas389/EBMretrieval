# EBMRetrieval — Deployment Guide v2

## 1. Termux Setup & GitHub Push

```bash
# Install packages
pkg update && pkg upgrade -y
pkg install python nodejs git -y

# Configure git
git config --global user.email "joysilas389@gmail.com"
git config --global user.name "Joysilas389"

# Navigate to project directory (after unzipping)
cd ebmretrieval

# Initialize repo
git init
git add .
git commit -m "EBMRetrieval v2: PostgreSQL, ICD-11, compare, animations, multilingual, PWA"
git branch -M main
git remote add origin https://github.com/Joysilas389/EBMretrieval.git

# Push (use --force if repo already has content)
git push -u origin main --force
```

If prompted for credentials, use a GitHub Personal Access Token:
1. Go to https://github.com/settings/tokens
2. Generate new token (classic) with `repo` scope
3. Use token as password when pushing

---

## 2. Database Setup (Already Done)

Your PostgreSQL is already provisioned on Render:
- **Service:** medscribe-db
- **Type:** PostgreSQL 18, Basic-256mb
- **Region:** Oregon (US West)
- **Internal URL:** `postgresql://medscribe_hcee_user:2hzupPdJmkAdCVZdtkemPZ1QrPiU1chr@dpg-d74g1j0gjchc73b6r2v0-a/medscribe_hcee`

The app will **drop old medscribe tables and create EBMRetrieval tables** on first deploy when `RESET_DB=true`.

After first successful deploy, change `RESET_DB` to `false` to prevent re-dropping.

---

## 3. Deploy Backend to Render

### Option A: From Dashboard
1. Go to https://dashboard.render.com/new/web-service
2. Connect GitHub repo `Joysilas389/EBMretrieval`
3. Configure:
   - **Name:** `ebmretrieval-api`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn api.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120`
4. Environment variables:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://medscribe_hcee_user:2hzupPdJmkAdCVZdtkemPZ1QrPiU1chr@dpg-d74g1j0gjchc73b6r2v0-a/medscribe_hcee` |
| `NCBI_EMAIL` | `joysilas389@gmail.com` |
| `NCBI_API_KEY` | (get free from https://www.ncbi.nlm.nih.gov/account/) |
| `FRONTEND_URL` | `https://ebmretrieval.vercel.app` (update after Vercel deploy) |
| `RESET_DB` | `true` (change to `false` after first deploy) |
| `CACHE_DIR` | `/tmp/pdf_cache` |

5. Deploy

### Option B: Using render.yaml
The repo includes `render.yaml` — Render can auto-detect this.

---

## 4. Deploy Frontend to Vercel

### From Dashboard
1. Go to https://vercel.com/new
2. Import `Joysilas389/EBMretrieval`
3. Configure:
   - **Root Directory:** `frontend`
   - **Framework:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Environment variable:
   - `VITE_API_URL` = `https://ebmretrieval-api.onrender.com/api`
   (replace with your actual Render backend URL)
5. Deploy

### Update vercel.json
After deploying backend, update `frontend/vercel.json` with your actual backend URL:
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://YOUR-BACKEND.onrender.com/api/$1" }
  ]
}
```

---

## 5. Post-Deploy Steps

### Seed the database
After backend is deployed, trigger seeding:
```bash
curl -X POST https://YOUR-BACKEND.onrender.com/api/admin/seed
```

This indexes ~100 PubMed articles across 25 medical topics.

### Reset DB (one-time)
If you need to reset the database:
```bash
curl -X POST https://YOUR-BACKEND.onrender.com/api/admin/reset-db
```

### Verify deployment
```bash
# Health check
curl https://YOUR-BACKEND.onrender.com/api/health

# Test search
curl -X POST https://YOUR-BACKEND.onrender.com/api/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "treatment for hypertension"}'

# Test ICD-11
curl "https://YOUR-BACKEND.onrender.com/api/icd?q=diabetes"

# Test compare
curl -X POST https://YOUR-BACKEND.onrender.com/api/compare \
  -H "Content-Type: application/json" \
  -d '{"condition_a": "asthma", "condition_b": "COPD"}'
```

---

## 6. Environment Variables Summary

### Backend (Render)
| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | **Yes** | PostgreSQL connection string |
| `NCBI_EMAIL` | Recommended | For PubMed API |
| `NCBI_API_KEY` | Recommended | Faster PubMed access (10 req/sec vs 3) |
| `FRONTEND_URL` | Yes | CORS origin |
| `RESET_DB` | First deploy | Set `true` once to init schema |
| `CACHE_DIR` | No | PDF cache dir (default: /tmp/pdf_cache) |

### Frontend (Vercel)
| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | **Yes** | Backend API URL |

---

## 7. Local Development

```bash
# Terminal 1 — Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://medscribe_hcee_user:2hzupPdJmkAdCVZdtkemPZ1QrPiU1chr@dpg-d74g1j0gjchc73b6r2v0-a/medscribe_hcee"
export RESET_DB=false
python -m api.main

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

---

## 8. Running Tests

```bash
cd backend
pip install pytest
python -m pytest tests/ -v
```

---

## 9. Updating After Deploy

```bash
# In Termux after making changes
cd ebmretrieval
git add .
git commit -m "description of changes"
git push

# Render auto-deploys from main branch
# Vercel auto-deploys from main branch
```

---

## 10. Existing Render Services

Your workspace has:
- **medscribe-api** — Python, Deployed (can be repurposed or kept separate)
- **medscribe-db** — PostgreSQL 18, Available ← **EBMRetrieval uses this**
- **smartmedicine-backend** — Node, Deployed

EBMRetrieval shares the `medscribe-db` PostgreSQL instance. The `RESET_DB=true` flag will drop
any existing medscribe tables and create fresh EBMRetrieval tables. Make sure you don't need the
old medscribe data before deploying.

---

## 11. Scaling Notes

The current setup handles moderate traffic. For scaling:
- Upgrade PostgreSQL plan on Render for more RAM/connections
- Add connection pooling (PgBouncer)
- Add Redis for response caching
- Scale backend to multiple Render instances
- Consider pgvector extension for production vector search
- Add CDN for static assets (Vercel does this automatically)
