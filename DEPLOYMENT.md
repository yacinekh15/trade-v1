# Deploying the Halal Crypto Scanner — all on Vercel (free)

Everything lives in one Vercel project: the dashboard (static page) and the
scanning logic (a Python serverless function) deploy together. Two small
free services fill in what serverless can't do on its own:

- **Upstash Redis** — holds scan results between requests (serverless functions don't remember anything between calls)
- **GitHub Actions** — triggers a scan every 5 minutes (Vercel's own free cron only runs once a day, too slow)

Trade-off vs. a real server: this is **near-live**, not instant — a new
scan lands roughly every 5 minutes rather than continuously. The dashboard
polls for updates every 25 seconds.

---

## 1. Create a free Upstash Redis database

1. Go to [upstash.com](https://upstash.com) → sign up → **Create Database**.
2. Pick the **Redis** type, any nearby region, leave it on the free plan.
3. On the database's page, copy the **REST URL** and **REST TOKEN** — you'll need both in step 3.

## 2. Push this project to GitHub

```bash
cd halal_scanner_vercel
git init
git add .
git commit -m "Halal crypto scanner - all-Vercel version"
# create a repo on GitHub, then:
git remote add origin <your-repo-url>
git push -u origin main
```

## 3. Deploy to Vercel

1. At [vercel.com](https://vercel.com) → **Add New → Project** → import the repo you just pushed.
2. Vercel auto-detects the Python function under `api/` and the static `index.html` — no build settings needed.
3. Before deploying, add these **Environment Variables** (Vercel project → Settings → Environment Variables):
   | Variable | Value |
   |---|---|
   | `UPSTASH_REDIS_REST_URL` | from step 1 |
   | `UPSTASH_REDIS_REST_TOKEN` | from step 1 |
   | `SCAN_SECRET` | make up any random string, e.g. `openssl rand -hex 16` |
   | `TELEGRAM_BOT_TOKEN` | optional, for alerts |
   | `TELEGRAM_CHAT_ID` | optional, for alerts |
4. Deploy. You'll get a URL like `https://your-scanner.vercel.app`.
5. Check `https://your-scanner.vercel.app/api/health` shows `{"status":"ok"}`.

## 4. Set up the free scheduler (GitHub Actions)

The workflow file is already in `.github/workflows/scan-cron.yml` — you just need to give it two secrets:

1. In your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**, add:
   - `VERCEL_APP_DOMAIN` = your Vercel domain **without** `https://`, e.g. `your-scanner.vercel.app`
   - `SCAN_SECRET` = the same random string you set on Vercel in step 3
2. That's it — GitHub will start running the scan every 5 minutes automatically once this is pushed. You can also trigger it manually: repo → **Actions** tab → "Trigger halal scanner scan" → **Run workflow**, to get your first scan immediately instead of waiting 5 minutes.

## 5. Open the dashboard

Visit `https://your-scanner.vercel.app`. The dashboard reads the most recent
cached scan and refreshes every 25 seconds. If no scan has run yet, it shows
"No results yet" until the GitHub Actions workflow runs. You can also trigger
the workflow manually from the Actions tab.

## Adjusting the scan frequency

Edit the `cron:` line in `.github/workflows/scan-cron.yml`:
- `*/5 * * * *` = every 5 minutes (default)
- `*/15 * * * *` = every 15 minutes, if you want to be extra conservative with Binance's rate limits

## Troubleshooting

- **Dashboard stuck on "No results yet"** → open `/api/health` directly; if that fails, check the Vercel deployment logs. If `/api/health` works but results don't appear, manually trigger the GitHub Action (step 4.2) and check its logs for the actual error.
- **`/api/results` returns an Upstash error** → verify `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` are configured in the Vercel Production environment.
- **Scanner import error** → the repository must contain `setup_score.py`; it provides the `score_symbol()` function used by `scanner.py`.
- **GitHub Action fails** → almost always a wrong `VERCEL_APP_DOMAIN` (no `https://`, no trailing slash) or mismatched `SCAN_SECRET` between GitHub and Vercel.
- **"invalid secret" from `/api/scan`** → the `secret` query param doesn't match `SCAN_SECRET` on Vercel — check for typos in either place.

## What's the same as before

- Binance Spot public market data only. The included Setup Score engine is a deterministic technical screening layer using the indicator calculations in `indicators_engine.py`.
- Setup Score is informational, never a trading instruction
- The earlier Telegram-only bot and the Railway+Vercel version still exist independently if you want to compare or switch back
