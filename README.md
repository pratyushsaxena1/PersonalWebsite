# personal-website

My personal site at pratyushsaxena.com. Hub, classic portfolio, and terminal portfolio in one Flask app.

## Stack

Flask, vanilla JS, SQLite for self-hosted analytics.

## Local development

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5001.

## Deploy

```bash
git push origin main
```

Then SSH into the host (GoDaddy cPanel → Terminal), pull, and restart:

```bash
cd ~/finalPersonalWebsite
git pull origin main
touch tmp/restart.txt
```
