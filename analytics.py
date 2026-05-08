"""Lightweight server-side analytics for the Flask portfolio.

No third-party scripts, no client cookies. Logs each non-bot request to a
SQLite file and emails a digest via Resend on demand.

Env vars:
  ANALYTICS_DB_PATH    Path to SQLite file (default: ./analytics.db)
  ADMIN_TOKEN          Required to hit /admin/report (generate a long random one)
  RESEND_API_KEY       Resend API key
  REPORT_TO_EMAIL      Recipient (default: pratyushsaxena4@gmail.com)
  REPORT_FROM_EMAIL    Sender (default: "Site Analytics <onboarding@resend.dev>")
"""

import hashlib
import json
import os
import re
import sqlite3
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone

DB_PATH = os.environ.get("ANALYTICS_DB_PATH", "analytics.db")

BOT_RE = re.compile(
    r"bot|crawler|spider|crawl|slurp|duckduck|baidu|yandex|prerender|"
    r"lighthouse|headless|httpclient|curl|wget|python-requests|axios|"
    r"facebookexternalhit|whatsapp|telegrambot|linkedinbot|twitterbot|"
    r"applebot|semrush|ahrefs|mj12bot",
    re.I,
)

SKIP_PREFIXES = ("/static/", "/favicon", "/robots.txt", "/admin/")

IP_SALT = os.environ.get("ANALYTICS_IP_SALT", "rotate-me")


def _hash_ip(ip: str) -> str:
    return hashlib.sha256((IP_SALT + "|" + (ip or "")).encode()).hexdigest()[:16]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hits (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        INTEGER NOT NULL,
                path      TEXT NOT NULL,
                referrer  TEXT,
                ua        TEXT,
                ip_hash   TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hits_ts ON hits(ts)")


def record(request) -> None:
    """Record a hit. Call from a Flask before_request hook."""
    try:
        path = request.path or "/"
        if path.startswith(SKIP_PREFIXES):
            return
        ua = (request.headers.get("User-Agent") or "")[:500]
        if BOT_RE.search(ua):
            return
        # X-Forwarded-For first hop, then remote_addr
        fwd = request.headers.get("X-Forwarded-For", "")
        ip = fwd.split(",")[0].strip() if fwd else (request.remote_addr or "")
        with _connect() as conn:
            conn.execute(
                "INSERT INTO hits(ts, path, referrer, ua, ip_hash) VALUES(?,?,?,?,?)",
                (
                    int(time.time()),
                    path[:300],
                    (request.referrer or "")[:500],
                    ua,
                    _hash_ip(ip),
                ),
            )
    except Exception:
        # Analytics must never break the request.
        pass


# ---------- reporting ----------

_BROWSERS = [
    ("Edge", r"Edg/"),
    ("Chrome", r"Chrome/"),
    ("Firefox", r"Firefox/"),
    ("Safari", r"Safari/"),
    ("Opera", r"OPR/|Opera/"),
]
_OSES = [
    ("iOS", r"iPhone|iPad"),
    ("Android", r"Android"),
    ("Mac", r"Mac OS X|Macintosh"),
    ("Windows", r"Windows NT"),
    ("Linux", r"Linux"),
]


def _parse_browser(ua: str) -> str:
    for name, pat in _BROWSERS:
        if re.search(pat, ua):
            return name
    return "Other"


def _parse_os(ua: str) -> str:
    for name, pat in _OSES:
        if re.search(pat, ua):
            return name
    return "Other"


def _domain(url: str) -> str:
    if not url:
        return "(direct)"
    m = re.match(r"https?://([^/]+)", url)
    return (m.group(1) if m else url)[:80]


def build_report(days: int = 7) -> dict:
    cutoff = int(time.time()) - days * 86400
    with _connect() as conn:
        rows = conn.execute(
            "SELECT ts, path, referrer, ua, ip_hash FROM hits WHERE ts >= ? ORDER BY ts",
            (cutoff,),
        ).fetchall()
        total_all = conn.execute("SELECT COUNT(*) AS c FROM hits").fetchone()["c"]

    pageviews = len(rows)
    uniques = len({r["ip_hash"] for r in rows})

    paths = Counter(r["path"] for r in rows).most_common(10)
    refs = Counter(_domain(r["referrer"]) for r in rows).most_common(10)
    browsers = Counter(_parse_browser(r["ua"] or "") for r in rows).most_common()
    oses = Counter(_parse_os(r["ua"] or "") for r in rows).most_common()

    # Hits per day
    by_day: Counter = Counter()
    for r in rows:
        d = datetime.fromtimestamp(r["ts"], tz=timezone.utc).strftime("%Y-%m-%d")
        by_day[d] += 1
    daily = sorted(by_day.items())

    return {
        "days": days,
        "pageviews": pageviews,
        "uniques": uniques,
        "top_paths": paths,
        "top_referrers": refs,
        "browsers": browsers,
        "oses": oses,
        "daily": daily,
        "total_lifetime_hits": total_all,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def _list_rows(items: list[tuple[str, int]]) -> str:
    if not items:
        return '<tr><td colspan="2" style="padding:4px 0;color:#9b9b9b">No data</td></tr>'
    out = []
    for label, n in items:
        out.append(
            f'<tr><td style="padding:3px 12px 3px 0;font-family:ui-monospace,monospace;font-size:13px">'
            f"{label}</td>"
            f'<td style="padding:3px 0;text-align:right;font-weight:600">{n}</td></tr>'
        )
    return "".join(out)


def render_html(report: dict) -> str:
    daily_html = "".join(
        f'<tr><td style="padding:3px 12px 3px 0;font-family:ui-monospace,monospace;font-size:13px">'
        f"{d}</td>"
        f'<td style="padding:3px 0;text-align:right;font-weight:600">{n}</td></tr>'
        for d, n in report["daily"]
    ) or '<tr><td colspan="2" style="color:#9b9b9b">No traffic in this window.</td></tr>'

    return f"""
<div style="font-family:system-ui,-apple-system,sans-serif;line-height:1.5;color:#1a1a1a;max-width:640px">
  <h2 style="margin:0 0 4px 0">pratyushsaxena.com — last {report['days']} days</h2>
  <p style="margin:0 0 24px 0;color:#6b6b6b;font-size:13px">Generated {report['generated_at']}</p>

  <div style="display:flex;gap:24px;margin-bottom:28px">
    <div>
      <div style="font-size:13px;color:#6b6b6b">Pageviews</div>
      <div style="font-size:32px;font-weight:600">{report['pageviews']}</div>
    </div>
    <div>
      <div style="font-size:13px;color:#6b6b6b">Unique visitors</div>
      <div style="font-size:32px;font-weight:600">{report['uniques']}</div>
    </div>
    <div>
      <div style="font-size:13px;color:#6b6b6b">Lifetime hits</div>
      <div style="font-size:32px;font-weight:600">{report['total_lifetime_hits']}</div>
    </div>
  </div>

  <h3 style="margin:24px 0 8px 0;font-size:14px;color:#6b6b6b;text-transform:uppercase;letter-spacing:0.05em">Top pages</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['top_paths'])}</table>

  <h3 style="margin:24px 0 8px 0;font-size:14px;color:#6b6b6b;text-transform:uppercase;letter-spacing:0.05em">Top referrers</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['top_referrers'])}</table>

  <h3 style="margin:24px 0 8px 0;font-size:14px;color:#6b6b6b;text-transform:uppercase;letter-spacing:0.05em">Hits per day</h3>
  <table style="border-collapse:collapse;width:100%">{daily_html}</table>

  <h3 style="margin:24px 0 8px 0;font-size:14px;color:#6b6b6b;text-transform:uppercase;letter-spacing:0.05em">Browsers</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['browsers'])}</table>

  <h3 style="margin:24px 0 8px 0;font-size:14px;color:#6b6b6b;text-transform:uppercase;letter-spacing:0.05em">Operating systems</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['oses'])}</table>

  <p style="margin:32px 0 0 0;font-size:12px;color:#9b9b9b">
    Local-only analytics — no cookies, no third-party scripts. IPs are hashed before storage.
  </p>
</div>
""".strip()


def render_text(report: dict) -> str:
    lines = [
        f"pratyushsaxena.com — last {report['days']} days",
        f"Generated {report['generated_at']}",
        "",
        f"Pageviews: {report['pageviews']}",
        f"Unique visitors: {report['uniques']}",
        f"Lifetime hits: {report['total_lifetime_hits']}",
        "",
        "Top pages:",
    ]
    for p, n in report["top_paths"]:
        lines.append(f"  {n:>4}  {p}")
    lines += ["", "Top referrers:"]
    for r, n in report["top_referrers"]:
        lines.append(f"  {n:>4}  {r}")
    lines += ["", "Hits per day:"]
    for d, n in report["daily"]:
        lines.append(f"  {d}  {n}")
    return "\n".join(lines)


def send_email(report: dict) -> tuple[bool, str]:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        return False, "RESEND_API_KEY not set"

    to_addr = os.environ.get("REPORT_TO_EMAIL", "pratyushsaxena4@gmail.com")
    from_addr = os.environ.get(
        "REPORT_FROM_EMAIL", "Site Analytics <onboarding@resend.dev>"
    )

    body = json.dumps(
        {
            "from": from_addr,
            "to": to_addr,
            "subject": (
                f"[pratyushsaxena.com] {report['pageviews']} views, "
                f"{report['uniques']} visitors — last {report['days']}d"
            ),
            "html": render_html(report),
            "text": render_text(report),
        }
    ).encode()

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "pratyushsaxena.com-analytics/1.0",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status < 300, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}"
    except Exception as e:
        return False, str(e)
