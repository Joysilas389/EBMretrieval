# EBMRetrieval — AI-Powered Evidence-Based Medicine Platform

An advanced medical evidence retrieval and synthesis platform that combines real-time source retrieval with AI-powered answer generation. Think of it as your own personal OpenEvidence.

**Live:** [ebmretrieval.vercel.app](https://ebmretrieval.vercel.app)

## What It Does

Ask any medical question — from clinical guidelines to drug dosing to pathophysiology — and get a comprehensive, structured, evidence-based answer with verified citations from real medical journals.

**Example queries:**
- "2025 hypertension guidelines"
- "Current dosing regimen for congestive heart failure"
- "Explain diabetic ketoacidosis from first principles"
- "Sickle cell disease in pregnancy management"
- "Compare ACEi vs ARB in diabetic nephropathy"

## Architecture

```
User Query
    ↓
Retrieval Layer (8 live sources in parallel)
    PubMed · NCBI Bookshelf · Europe PMC · MedlinePlus
    WHO · CDC · OpenFDA · PostgreSQL Index
    ↓
Claude AI Synthesis Layer
    ↓ Claude also searches the web for:
    Systematic reviews · Meta-analyses · Clinical guidelines
    NEJM · Lancet · JAMA · BMJ · Cochrane · Society guidelines
    ↓
Structured Answer with Inline Citation Badges
    + Reference list at bottom (max 15, last 5 years priority)
    + Guideline / Meta-Analysis / New tags on each reference
```

## Key Features

- **AI-Powered Answers** — Claude synthesizes evidence into structured, clinician-level responses
- **Dynamic Response Structure** — Claude adapts to the question (dosing query gets dosing, explanation query gets teaching)
- **Web Search for Sources** — Claude searches beyond the 8 retrieval sources for systematic reviews, meta-analyses, and guidelines
- **OpenEvidence-Style Citations** — Inline colored badges (NEJM, Lancet, WHO) + numbered reference cards at bottom
- **20 Interactive Simulations** — Cardiac cycle, action potential, coagulation cascade, Krebs cycle, RAAS, and more with SVG visuals
- **AI-Generated Simulations** — Type any medical topic and Claude generates an interactive step-by-step simulation with SVG diagrams
- **Teaching Mode** — First-principles explanations with mechanism → clinical bridge
- **Compare Conditions** — Side-by-side evidence comparison
- **ICD-11 Classification** — Search and browse ICD-11 codes
- **History & Bookmarks** — Local storage, no login required
- **Dark/Light Mode** — Professional medical UI
- **Mobile-First** — Optimized for phone use

## Tech Stack

**Frontend:** React + Vite + TypeScript → Vercel
**Backend:** Python FastAPI → Render
**Database:** PostgreSQL (Render)
**AI:** Claude API (Sonnet) with web search tool
**Sources:** PubMed Entrez API, Europe PMC, MedlinePlus XML, WHO, CDC, OpenFDA, NCBI Bookshelf

## Environment Variables

### Render (Backend)
```
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-...
NCBI_EMAIL=your@email.com
FRONTEND_URL=*
```

### Vercel (Frontend)
```
VITE_API_URL=https://your-backend.onrender.com/api
```

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL="postgresql://..."
export ANTHROPIC_API_KEY="sk-ant-..."
export NCBI_EMAIL="your@email.com"
uvicorn api.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deployment

### Push to GitHub (from Termux)
```bash
cd ~/ebmretrieval
git init
git add .
git commit -m "deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/EBMretrieval.git
git push -u origin main --force
```

### Vercel
1. Import repo on vercel.com
2. Set root directory to `frontend`
3. Set framework to Vite
4. Add env var: `VITE_API_URL`

### Render
1. Create Web Service from repo
2. Set root directory to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn api.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120`
5. Add env vars: `DATABASE_URL`, `ANTHROPIC_API_KEY`, `NCBI_EMAIL`

## How Answers Are Generated

1. **Retrieval** — 8 sources queried in parallel for relevant evidence
2. **Topic Filtering** — Off-topic chunks rejected based on query subject
3. **Claude Synthesis** — Claude receives retrieved evidence + searches web for additional high-quality sources
4. **Dynamic Structure** — Claude adapts response to the question (not a rigid template)
5. **Citation Verification** — Only real, verifiable sources cited with URLs
6. **Fallback** — If Claude API is unavailable, extractive assembly from retrieved evidence

## Interactive Simulations (20 Pre-Built)

**Physiology:** Cardiac Cycle, Action Potential, Coagulation Cascade, Nephron Function, RAAS, O2-Hemoglobin Curve, Acid-Base, Muscle Contraction

**Biochemistry:** Krebs Cycle, Electron Transport Chain, Glycolysis, Gluconeogenesis, Beta-Oxidation, Urea Cycle, Heme Synthesis

**Embryology:** Gastrulation, Neural Tube, Heart Development, Pharyngeal Arches, Kidney Development

Each simulation has step-by-step phases with deep first-principles explanations and clinical bedside applications.

## Disclaimer

For educational and clinical reference purposes only. Does not replace professional medical judgment. Always verify critical clinical decisions with current guidelines and specialist consultation.

## License

MIT
