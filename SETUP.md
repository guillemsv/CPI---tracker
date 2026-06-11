# SETUP GUIDE — 5 minutes, no experience needed

## Step 1 — Get your free API keys (3 minutes)

### EIA API key (energy prices)
1. Go to https://www.eia.gov/opendata/register.php
2. Enter your email → they email you a key instantly
3. Looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### FRED API key (economic data)
1. Go to https://fredaccount.stlouisfed.org/login/secure/
2. Create free account → My Account → API Keys → Request API Key
3. Looks like: `abcdef1234567890abcdef1234567890`

### BLS API key (official CPI benchmark) — optional but recommended
1. Go to https://data.bls.gov/registrationEngine/
2. Register free → key emailed to you

---

## Step 2 — Create your GitHub repo (1 minute)

1. Go to https://github.com and create a free account
2. Click the **+** button (top right) → **New repository**
3. Name it: `cpi-tracker`
4. Set to **Public** (required for free GitHub Pages)
5. Click **Create repository**

---

## Step 3 — Upload the code (1 minute)

### Option A — GitHub Desktop (easiest, no terminal)
1. Download GitHub Desktop: https://desktop.github.com
2. File → Clone Repository → paste your repo URL
3. Copy all files from this folder into the cloned folder
4. Click **Commit to main** → **Push origin**

### Option B — Terminal (if you have Python already)
```bash
cd cpi-tracker
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/cpi-tracker.git
git push -u origin main
```

---

## Step 4 — Add your API keys as GitHub Secrets (1 minute)

This keeps your keys private even in a public repo.

1. Go to your repo on GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

| Name | Value |
|------|-------|
| `EIA_API_KEY` | your EIA key |
| `FRED_API_KEY` | your FRED key |
| `BLS_API_KEY` | your BLS key (or leave blank) |

---

## Step 5 — Enable GitHub Pages (dashboard)

1. Repo **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** → folder: **/dashboard**
4. Click Save
5. Your dashboard will be live at: `https://YOUR_USERNAME.github.io/cpi-tracker`

---

## Step 6 — Trigger first run

1. Go to **Actions** tab in your repo
2. Click **Daily CPI Update** workflow
3. Click **Run workflow** → **Run workflow**
4. Watch it run live (takes ~2 minutes)
5. After it finishes, check `output/cpi_latest.json` in your repo

From now on it runs automatically every day at 08:00 UTC.

---

## Troubleshooting

**Action fails with "API key not found"** → Check Step 4, make sure secret names match exactly

**Dashboard shows no data** → Run the workflow manually first (Step 6)

**Zillow data missing** → Zillow CSV URL sometimes changes; check scrapers/zillow.py and update URL
