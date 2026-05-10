# Personal Website

Notes for future me. Two separate projects, two separate hosts, two separate repos.

## What's where

| Project | Lives at | Hosted on | Repo |
|---|---|---|---|
| Flask portfolio | pratyushsaxena.com | GoDaddy (cPanel + Setup Python App) | [PersonalWebsite](https://github.com/pratyushsaxena1/PersonalWebsite) |
| Next.js tools hub | tools.pratyushsaxena.com | Vercel | [tools](https://github.com/pratyushsaxena1/tools) |

The freeTools folder inside this repo is gitignored. It has its own repo and its own deploy.

## Updating the Flask site (pratyushsaxena.com)

1. Make changes locally, commit, and push to GitHub.
   ```
   git add .
   git commit -m "what changed"
   git push origin main
   ```
2. SSH into GoDaddy:
   - godaddy.com → My Products → Web Hosting → Manage → cPanel Admin
   - cPanel → Advanced → Terminal
3. Pull and restart:
   ```
   cd ~/finalPersonalWebsite
   git pull origin main
   touch tmp/restart.txt
   ```
4. If `requirements.txt` changed, also run:
   ```
   source ~/virtualenv/finalPersonalWebsite/3.11/bin/activate
   pip install -r requirements.txt
   ```
   (Adjust the Python version in the path if needed.)
5. Restart for env-var changes: cPanel → Setup Python App → click the app → orange Restart button.
6. Verify: open pratyushsaxena.com in incognito.

## Updating the tools hub (tools.pratyushsaxena.com)

Just push to GitHub. Vercel auto-deploys on every push to `main`.

```
cd freeTools
git add .
git commit -m "what changed"
git push origin main
```

Watch the deploy at vercel.com. Done in about a minute.

## Seeing visitor stats

### Flask site (server-side, no cookies)

I built an analytics layer in `analytics.py`. It logs every non-bot pageview to a SQLite file with a hashed IP for unique-visitor counts. The report shows pageviews and visitors broken down by window (24h / 7d / 30d / 90d / 365d / all-time), top pages, top referrers, referrer category (search / social / direct / etc), browsers, OSes, devices, hour-of-day, day-of-week, busiest day/hour/weekday, and bar charts of daily / weekly / monthly hits.

To see the full report in the browser:
```
https://pratyushsaxena.com/admin/report?token=YOUR_ADMIN_TOKEN
```

To get it as JSON:
```
https://pratyushsaxena.com/admin/report?token=YOUR_ADMIN_TOKEN&format=json
```

To send the report to my email via Resend:
```
https://pratyushsaxena.com/admin/report?token=YOUR_ADMIN_TOKEN&email=1
```

To change the trend-window (defaults to last 7 days for the trend tables; the snapshot cards always show all windows):
```
https://pratyushsaxena.com/admin/report?token=YOUR_ADMIN_TOKEN&days=365
```

Max accepted is 3650. The token lives in the cPanel env var `ADMIN_TOKEN`. Without it, the endpoint silently 404s.

### Auto-email weekly

I use cron-job.org to hit the email URL on a schedule. Free.

1. cron-job.org → Create cronjob.
2. URL: the email URL above with the real token.
3. Schedule: Monday 9am.
4. Save.

### Tools hub (Vercel Analytics)

Already wired up via `@vercel/analytics`. Just open vercel.com → freeTools project → Analytics tab. Free tier covers pageviews, top pages, referrers, devices, countries.

## Environment variables

Real values live on the servers, not in this repo.

### GoDaddy (Flask, set in cPanel → Setup Python App → Environment variables)

| Variable | What it does |
|---|---|
| `ADMIN_TOKEN` | Required to hit `/admin/report`. Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `RESEND_API_KEY` | Resend API key for the analytics email |
| `REPORT_TO_EMAIL` | Where the email goes. Defaults to pratyushsaxena4@gmail.com |
| `REPORT_FROM_EMAIL` | Sender. Defaults to `Site Analytics <onboarding@resend.dev>` |
| `ANALYTICS_DB_PATH` | Optional. Where the SQLite file lives. Default is `analytics.db` next to `app.py` |
| `ANALYTICS_IP_SALT` | Optional. Salt for the IP hash. Rotate occasionally if paranoid |

### Vercel (freeTools, set in project → Settings → Environment Variables)

| Variable | What it does |
|---|---|
| `RESEND_API_KEY` | For the "request a tool" form email |
| `REQUEST_TO_EMAIL` | Where requests go. Defaults to pratyushsaxena4@gmail.com |
| `REQUEST_FROM_EMAIL` | Sender. Defaults to `Tools Hub <onboarding@resend.dev>` |

If you change Vercel env vars, redeploy from the Deployments tab for them to take effect.

### Resend free-tier gotcha

Using `onboarding@resend.dev` as the from address only lets you send to the email you signed up to Resend with. To send to other addresses, verify the domain in Resend (DNS records on GoDaddy) and switch `REPORT_FROM_EMAIL` / `REQUEST_FROM_EMAIL` to something like `Site <noreply@pratyushsaxena.com>`.

## Local development

### Flask site

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open localhost:5001. The analytics SQLite file gets created in the project folder.

### Tools hub

```
cd freeTools
npm install
npm run dev
```

Open localhost:3000. To test the request-tool form locally, copy `.env.example` to `.env.local` and add your Resend key.

## File layout

```
.
├── app.py                  Flask app (routes, content, redirects)
├── analytics.py            Server-side analytics + Resend digest email
├── requirements.txt
├── Procfile                Used by some hosts. GoDaddy uses Passenger.
├── templates/
│   ├── landing.html        /
│   ├── classic/index.html  /classic
│   └── terminal/           /terminal, /terminal/experience, etc.
├── static/
│   ├── css/, js/
│   └── resume.pdf
└── freeTools/              (separate repo, own README)
```

## Useful one-liners

Generate a new ADMIN_TOKEN:
```
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

See last commit on the GoDaddy server (run after SSHing in):
```
cd ~/finalPersonalWebsite && git log -1 --oneline
```

Reset the analytics database (start fresh):
```
rm ~/finalPersonalWebsite/analytics.db && touch ~/finalPersonalWebsite/tmp/restart.txt
```

Trigger a fresh Vercel deploy without code changes:
```
cd freeTools && git commit --allow-empty -m "redeploy" && git push
```

## Things to remember

- Never commit `.env`, `.env.local`, or `analytics.db`. Both are gitignored.
- Rotating the Resend key: do it in resend.com, then update the env var in both Vercel and cPanel.
- The Flask site's git remote on GoDaddy is fetched over HTTPS with a personal access token (GitHub → Settings → Developer settings → Tokens classic, `repo` scope). If pulls start failing with auth errors, the token expired.
- cPanel sometimes only loads new env vars after the orange Restart button. `touch tmp/restart.txt` reloads code, not env vars.
