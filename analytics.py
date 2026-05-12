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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hits_ip ON hits(ip_hash)")
        # Separate table for the tools subdomain (tools.pratyushsaxena.com).
        # Keeps the main portfolio analytics clean and lets us count unique
        # visitors specifically for the tools site.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_hits (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        INTEGER NOT NULL,
                slug      TEXT,
                referrer  TEXT,
                ua        TEXT,
                ip_hash   TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_hits_ts ON tool_hits(ts)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_hits_ip ON tool_hits(ip_hash)")


def record(request) -> None:
    """Record a hit. Call from a Flask before_request hook."""
    try:
        path = request.path or "/"
        if path.startswith(SKIP_PREFIXES):
            return
        ua = (request.headers.get("User-Agent") or "")[:500]
        if BOT_RE.search(ua):
            return
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


def record_tool_hit(request, slug: str | None = None) -> None:
    """Record a hit on the tools subdomain. Called from the public CORS endpoint."""
    try:
        ua = (request.headers.get("User-Agent") or "")[:500]
        if BOT_RE.search(ua):
            return
        fwd = request.headers.get("X-Forwarded-For", "")
        ip = fwd.split(",")[0].strip() if fwd else (request.remote_addr or "")
        with _connect() as conn:
            conn.execute(
                "INSERT INTO tool_hits(ts, slug, referrer, ua, ip_hash) VALUES(?,?,?,?,?)",
                (
                    int(time.time()),
                    (slug or "")[:200] or None,
                    (request.referrer or "")[:500],
                    ua,
                    _hash_ip(ip),
                ),
            )
    except Exception:
        pass


def tool_visit_stats() -> dict:
    """Total visits + unique visitors across the whole brand (main site +
    tools subdomain). Counts everything, including API tracker calls, so
    the headline number reflects total touchpoints, not just user-facing
    pageviews."""
    try:
        with _connect() as conn:
            tool_visits = conn.execute("SELECT COUNT(*) FROM tool_hits").fetchone()[0] or 0
            main_visits = conn.execute("SELECT COUNT(*) FROM hits").fetchone()[0] or 0
            unique_visitors = conn.execute(
                "SELECT COUNT(DISTINCT ip_hash) FROM ("
                "  SELECT ip_hash FROM hits "
                "  UNION SELECT ip_hash FROM tool_hits"
                ")"
            ).fetchone()[0] or 0
            return {
                "visits": int(tool_visits + main_visits),
                "visitors": int(unique_visitors),
            }
    except Exception:
        return {"visits": 0, "visitors": 0}


# ---------- parsing helpers ----------

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
_DEVICE_MOBILE = re.compile(r"Mobile|iPhone|Android(?!.*Tablet)", re.I)
_DEVICE_TABLET = re.compile(r"iPad|Tablet", re.I)

_DOW_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


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


def _parse_device(ua: str) -> str:
    if _DEVICE_TABLET.search(ua):
        return "Tablet"
    if _DEVICE_MOBILE.search(ua):
        return "Mobile"
    return "Desktop"


def _domain(url: str) -> str:
    if not url:
        return "(direct)"
    m = re.match(r"https?://([^/]+)", url)
    return (m.group(1) if m else url)[:80]


def _classify_referrer(host: str) -> str:
    if host == "(direct)":
        return "Direct"
    h = host.lower()
    if any(s in h for s in ("google.", "bing.", "duckduckgo.", "yahoo.", "yandex.", "baidu.")):
        return "Search"
    if any(s in h for s in (
        "twitter.", "x.com", "t.co", "facebook.", "fb.com", "instagram.",
        "linkedin.", "lnkd.", "reddit.", "youtube.", "tiktok.", "pinterest.",
        "discord.", "mastodon.", "threads.",
    )):
        return "Social"
    if any(s in h for s in ("github.", "gitlab.", "stackoverflow.", "ycombinator.", "news.")):
        return "Tech & News"
    return "Other"


def _bucket_window(rows, days: int):
    """Slice rows down to the last N days. days=0 means all time."""
    if days <= 0:
        return rows
    cutoff = int(time.time()) - days * 86400
    return [r for r in rows if r["ts"] >= cutoff]


def _window_summary(rows) -> dict:
    pageviews = len(rows)
    uniques = len({r["ip_hash"] for r in rows})
    avg = pageviews / uniques if uniques else 0
    visit_counts = Counter(r["ip_hash"] for r in rows)
    returning = sum(1 for c in visit_counts.values() if c > 1)
    new = uniques - returning
    return {
        "pageviews": pageviews,
        "uniques": uniques,
        "returning": returning,
        "new": new,
        "avg_per_visitor": round(avg, 2),
    }


# ---------- main report ----------

def build_report(days: int = 7) -> dict:
    """Build a comprehensive analytics report covering everything we know."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT ts, path, referrer, ua, ip_hash FROM hits ORDER BY ts"
        ).fetchall()

    if not rows:
        return {
            "days": days,
            "windows": {},
            "empty": True,
            "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

    first_ts = rows[0]["ts"]
    last_ts = rows[-1]["ts"]
    first_dt = datetime.fromtimestamp(first_ts, tz=timezone.utc)
    last_dt = datetime.fromtimestamp(last_ts, tz=timezone.utc)
    age_days = max(1, (int(time.time()) - first_ts) // 86400)

    # Multi-window summaries
    windows = {}
    for label, n in (("24h", 1), ("7d", 7), ("30d", 30), ("90d", 90), ("365d", 365), ("all", 0)):
        bucket = _bucket_window(rows, n)
        if not bucket and label != "all":
            continue
        windows[label] = _window_summary(bucket)

    # Lifetime breakdowns (using the rows in the requested days window for trend stuff)
    win_rows = _bucket_window(rows, days)
    if not win_rows:
        win_rows = rows  # fall back to all if requested window is empty

    paths = Counter(r["path"] for r in win_rows).most_common(20)
    refs_raw = [_domain(r["referrer"]) for r in win_rows]
    refs = Counter(refs_raw).most_common(20)
    ref_classes = Counter(_classify_referrer(d) for d in refs_raw).most_common()

    browsers = Counter(_parse_browser(r["ua"] or "") for r in win_rows).most_common()
    oses = Counter(_parse_os(r["ua"] or "") for r in win_rows).most_common()
    devices = Counter(_parse_device(r["ua"] or "") for r in win_rows).most_common()

    # Time-of-day and day-of-week buckets (in UTC; close enough)
    by_hour = Counter()
    by_dow = Counter()
    by_day = Counter()
    by_week = Counter()
    by_month = Counter()
    for r in win_rows:
        d = datetime.fromtimestamp(r["ts"], tz=timezone.utc)
        by_hour[d.hour] += 1
        by_dow[d.weekday()] += 1
        by_day[d.strftime("%Y-%m-%d")] += 1
        # ISO week
        iso_year, iso_week, _ = d.isocalendar()
        by_week[f"{iso_year}-W{iso_week:02d}"] += 1
        by_month[d.strftime("%Y-%m")] += 1

    daily = sorted(by_day.items())
    weekly = sorted(by_week.items())
    monthly = sorted(by_month.items())
    hourly = [(h, by_hour.get(h, 0)) for h in range(24)]
    dow = [(_DOW_NAMES[i], by_dow.get(i, 0)) for i in range(7)]

    busiest_day = max(by_day.items(), key=lambda x: x[1]) if by_day else None
    busiest_hour = max(by_hour.items(), key=lambda x: x[1]) if by_hour else None
    busiest_dow = (
        max(by_dow.items(), key=lambda x: x[1]) if by_dow else None
    )
    busiest_dow_named = (
        (_DOW_NAMES[busiest_dow[0]], busiest_dow[1]) if busiest_dow else None
    )

    # Referrer URLs (full, not just domain), top 15
    full_refs = [r["referrer"] for r in win_rows if r["referrer"]]
    top_full_refs = Counter(full_refs).most_common(15)

    # Lifetime stats
    lifetime = {
        "first_hit": first_dt.strftime("%Y-%m-%d"),
        "last_hit": last_dt.strftime("%Y-%m-%d"),
        "total_hits": len(rows),
        "total_uniques": len({r["ip_hash"] for r in rows}),
        "tracked_days": age_days,
        "avg_hits_per_day": round(len(rows) / age_days, 1) if age_days else 0,
    }

    return {
        "days": days,
        "empty": False,
        "windows": windows,
        "lifetime": lifetime,
        "top_paths": paths,
        "top_referrers": refs,
        "top_full_referrers": top_full_refs,
        "referrer_classes": ref_classes,
        "browsers": browsers,
        "oses": oses,
        "devices": devices,
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "hourly": hourly,
        "dow": dow,
        "busiest_day": busiest_day,
        "busiest_hour": busiest_hour,
        "busiest_dow": busiest_dow_named,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


# ---------- HTML rendering ----------

_LABEL_STYLE = (
    "padding:3px 12px 3px 0;font-family:ui-monospace,"
    "monospace;font-size:13px;color:#1a1a1a"
)
_VALUE_STYLE = "padding:3px 0;text-align:right;font-weight:600;font-variant-numeric:tabular-nums"
_HEADER = (
    "margin:32px 0 8px 0;font-size:13px;color:#6b6b6b;"
    "text-transform:uppercase;letter-spacing:0.06em;font-weight:600"
)


def _list_rows(items, max_label=64) -> str:
    if not items:
        return f'<tr><td colspan="2" style="padding:6px 0;color:#9b9b9b">No data</td></tr>'
    out = []
    total = sum(n for _, n in items) or 1
    for label, n in items:
        s = str(label)
        if len(s) > max_label:
            s = s[:max_label] + "..."
        pct = (n / total) * 100
        out.append(
            f'<tr>'
            f'<td style="{_LABEL_STYLE}">{s}</td>'
            f'<td style="{_VALUE_STYLE}">{n}'
            f' <span style="color:#9b9b9b;font-weight:400;font-size:12px">({pct:.0f}%)</span>'
            f'</td></tr>'
        )
    return "".join(out)


def _bar_rows(items, max_val=None) -> str:
    if not items:
        return ""
    if max_val is None:
        max_val = max((n for _, n in items), default=1) or 1
    out = []
    for label, n in items:
        width = (n / max_val) * 100 if max_val else 0
        out.append(
            f'<tr>'
            f'<td style="{_LABEL_STYLE};white-space:nowrap;width:80px">{label}</td>'
            f'<td style="padding:3px 0;width:100%">'
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<div style="background:#0a7;height:10px;border-radius:2px;width:{width:.1f}%;min-width:1px"></div>'
            f'<span style="font-size:12px;font-variant-numeric:tabular-nums">{n}</span>'
            f'</div>'
            f'</td></tr>'
        )
    return "".join(out)


def _window_card(label: str, w: dict) -> str:
    return f"""
    <td style="padding:12px;border:1px solid #ececec;border-radius:8px;vertical-align:top">
      <div style="font-size:11px;color:#6b6b6b;text-transform:uppercase;letter-spacing:0.05em;font-weight:600;margin-bottom:6px">{label}</div>
      <div style="font-size:24px;font-weight:600;line-height:1">{w['pageviews']}</div>
      <div style="font-size:11px;color:#6b6b6b;margin-top:2px">pageviews</div>
      <div style="margin-top:10px;font-size:13px;font-variant-numeric:tabular-nums">
        <div><span style="color:#6b6b6b">Visitors</span> &nbsp; <strong>{w['uniques']}</strong></div>
        <div><span style="color:#6b6b6b">Returning</span> &nbsp; <strong>{w['returning']}</strong></div>
        <div><span style="color:#6b6b6b">Avg / visitor</span> &nbsp; <strong>{w['avg_per_visitor']}</strong></div>
      </div>
    </td>
    """


def render_html(report: dict) -> str:
    if report.get("empty"):
        return f"""
        <div style="font-family:system-ui,sans-serif;padding:40px;color:#1a1a1a">
          <h2>pratyushsaxena.com analytics</h2>
          <p style="color:#6b6b6b">No data yet. Visit the site to start collecting hits.</p>
          <p style="color:#9b9b9b;font-size:12px">Generated {report['generated_at']}</p>
        </div>
        """.strip()

    w = report["windows"]
    lifetime = report["lifetime"]

    # Window cards row
    window_cards = ""
    for label in ("24h", "7d", "30d", "90d", "365d", "all"):
        if label in w:
            window_cards += _window_card(label, w[label])

    busiest_lines = []
    if report.get("busiest_day"):
        d, n = report["busiest_day"]
        busiest_lines.append(f"<div><span style='color:#6b6b6b'>Busiest day</span> <strong>{d}</strong> ({n} hits)</div>")
    if report.get("busiest_hour") is not None:
        h, n = report["busiest_hour"]
        busiest_lines.append(f"<div><span style='color:#6b6b6b'>Busiest hour</span> <strong>{h:02d}:00 UTC</strong> ({n} hits)</div>")
    if report.get("busiest_dow"):
        d, n = report["busiest_dow"]
        busiest_lines.append(f"<div><span style='color:#6b6b6b'>Busiest weekday</span> <strong>{d}</strong> ({n} hits)</div>")

    # Trim daily/weekly to keep email reasonable
    daily_recent = report["daily"][-60:]
    weekly_all = report["weekly"][-26:]
    monthly_all = report["monthly"][-24:]

    return f"""
<div style="font-family:system-ui,-apple-system,sans-serif;line-height:1.5;color:#1a1a1a;max-width:760px;padding:0 4px">
  <h2 style="margin:0 0 4px 0">pratyushsaxena.com analytics</h2>
  <p style="margin:0 0 24px 0;color:#6b6b6b;font-size:13px">
    Generated {report['generated_at']} &middot; tracked since {lifetime['first_hit']} ({lifetime['tracked_days']} days)
  </p>

  <h3 style="{_HEADER}">Snapshot by window</h3>
  <table style="border-collapse:separate;border-spacing:8px;width:100%">
    <tr>{window_cards}</tr>
  </table>

  <h3 style="{_HEADER}">Lifetime totals</h3>
  <table style="border-collapse:collapse;width:100%">
    <tr><td style="{_LABEL_STYLE}">First hit</td><td style="{_VALUE_STYLE}">{lifetime['first_hit']}</td></tr>
    <tr><td style="{_LABEL_STYLE}">Last hit</td><td style="{_VALUE_STYLE}">{lifetime['last_hit']}</td></tr>
    <tr><td style="{_LABEL_STYLE}">Total pageviews</td><td style="{_VALUE_STYLE}">{lifetime['total_hits']}</td></tr>
    <tr><td style="{_LABEL_STYLE}">Total unique visitors</td><td style="{_VALUE_STYLE}">{lifetime['total_uniques']}</td></tr>
    <tr><td style="{_LABEL_STYLE}">Days tracked</td><td style="{_VALUE_STYLE}">{lifetime['tracked_days']}</td></tr>
    <tr><td style="{_LABEL_STYLE}">Avg hits / day</td><td style="{_VALUE_STYLE}">{lifetime['avg_hits_per_day']}</td></tr>
  </table>

  {('<h3 style="' + _HEADER + '">Highlights</h3><div style="font-size:14px;line-height:1.8;font-variant-numeric:tabular-nums">' + "".join(busiest_lines) + '</div>') if busiest_lines else ''}

  <h3 style="{_HEADER}">Top pages (last {report['days']} days)</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['top_paths'])}</table>

  <h3 style="{_HEADER}">Top referring domains</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['top_referrers'])}</table>

  <h3 style="{_HEADER}">Referrer category</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['referrer_classes'])}</table>

  <h3 style="{_HEADER}">Hits per day (last 60)</h3>
  <table style="border-collapse:collapse;width:100%">{_bar_rows(daily_recent)}</table>

  <h3 style="{_HEADER}">Hits per week (last 26)</h3>
  <table style="border-collapse:collapse;width:100%">{_bar_rows(weekly_all)}</table>

  <h3 style="{_HEADER}">Hits per month</h3>
  <table style="border-collapse:collapse;width:100%">{_bar_rows(monthly_all)}</table>

  <h3 style="{_HEADER}">Hour of day (UTC)</h3>
  <table style="border-collapse:collapse;width:100%">{_bar_rows([(f'{h:02d}:00', n) for h, n in report['hourly']])}</table>

  <h3 style="{_HEADER}">Day of week</h3>
  <table style="border-collapse:collapse;width:100%">{_bar_rows(report['dow'])}</table>

  <h3 style="{_HEADER}">Devices</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['devices'])}</table>

  <h3 style="{_HEADER}">Browsers</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['browsers'])}</table>

  <h3 style="{_HEADER}">Operating systems</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['oses'])}</table>

  <h3 style="{_HEADER}">Top full referrer URLs</h3>
  <table style="border-collapse:collapse;width:100%">{_list_rows(report['top_full_referrers'], max_label=80)}</table>

  <p style="margin:40px 0 0 0;font-size:11px;color:#9b9b9b;border-top:1px solid #ececec;padding-top:12px">
    Local analytics. No cookies, no third-party scripts. IPs are hashed before storage.
    Set the <code>days</code> query param to change the time window
    (e.g. <code>?days=30</code> or <code>?days=365</code>).
  </p>
</div>
""".strip()


def render_text(report: dict) -> str:
    if report.get("empty"):
        return "No analytics data yet."

    lifetime = report["lifetime"]
    lines = [
        "pratyushsaxena.com analytics",
        f"Generated {report['generated_at']}",
        f"Tracked since {lifetime['first_hit']} ({lifetime['tracked_days']} days)",
        "",
        "By window:",
    ]
    for label in ("24h", "7d", "30d", "90d", "365d", "all"):
        if label in report["windows"]:
            wd = report["windows"][label]
            lines.append(
                f"  {label:>5}: {wd['pageviews']:>5} views, {wd['uniques']:>4} visitors, "
                f"{wd['returning']:>3} returning"
            )
    lines += [
        "",
        f"Lifetime: {lifetime['total_hits']} hits, {lifetime['total_uniques']} visitors, "
        f"{lifetime['avg_hits_per_day']}/day avg",
        "",
        "Top pages:",
    ]
    for p, n in report["top_paths"][:10]:
        lines.append(f"  {n:>4}  {p}")
    lines += ["", "Top referrers:"]
    for r, n in report["top_referrers"][:10]:
        lines.append(f"  {n:>4}  {r}")
    lines += ["", "Hits per day (last 30):"]
    for d, n in report["daily"][-30:]:
        lines.append(f"  {d}  {n}")
    return "\n".join(lines)


# ---------- email ----------

def send_email(report: dict) -> tuple[bool, str]:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        return False, "RESEND_API_KEY not set"

    to_addr = os.environ.get("REPORT_TO_EMAIL", "pratyushsaxena4@gmail.com")
    from_addr = os.environ.get(
        "REPORT_FROM_EMAIL", "Site Analytics <onboarding@resend.dev>"
    )

    if report.get("empty"):
        subject = "[pratyushsaxena.com] No traffic data yet"
    else:
        w = report["windows"].get("7d") or report["windows"].get("all", {})
        subject = (
            f"[pratyushsaxena.com] {w.get('pageviews', 0)} views, "
            f"{w.get('uniques', 0)} visitors (last 7d)"
        )

    body = json.dumps(
        {
            "from": from_addr,
            "to": to_addr,
            "subject": subject,
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
