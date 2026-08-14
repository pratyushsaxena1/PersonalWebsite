import hmac
import os
import threading
import time
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, abort, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

import analytics

app = Flask(__name__)

# Trust exactly one proxy hop (the platform load balancer) for X-Forwarded-For /
# -Proto / -Host. Without this, request.remote_addr is the proxy and the raw
# header is client-spoofable; with it, remote_addr is the real client IP that
# the trusted proxy appended, which the rate limiter and analytics rely on.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

analytics.init_db()


# Lightweight in-process rate limiter (no external store). Per-worker under
# gunicorn, so it's a best-effort flood brake rather than a hard global cap;
# enough to stop a single client from hammering the public analytics-write
# endpoint and bloating the SQLite DB. Strong limits would need a shared store
# or a WAF rule at the platform edge.
_rl_lock = threading.Lock()
_rl_hits: dict[str, list[float]] = {}


def _rate_limited(key: str, limit: int, window_s: float) -> bool:
    now = time.time()
    with _rl_lock:
        bucket = [t for t in _rl_hits.get(key, []) if now - t < window_s]
        bucket.append(now)
        _rl_hits[key] = bucket
        if len(_rl_hits) > 10000:  # bound memory under IP-spray
            for k in [k for k, v in _rl_hits.items() if not v or now - v[-1] > window_s]:
                _rl_hits.pop(k, None)
        return len(bucket) > limit


@app.before_request
def _log_hit():
    analytics.record(request)


# Content-Security-Policy: the site only loads Google Fonts externally and has a
# few inline <script>/<style> blocks, so inline is allowed but external scripts
# are not. frame-ancestors blocks clickjacking.
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


@app.after_request
def _security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    resp.headers.setdefault(
        "Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload"
    )
    resp.headers.setdefault("Content-Security-Policy", _CSP)
    return resp


SITE = {
    "name": "Pratyush Saxena",
    "first_name": "Pratyush",
    "role": "CS + AI @ Cornell",
    "location": "Ithaca, NY",
    "email": "pratyushsaxena4@gmail.com",
    "github": "https://github.com/pratyushsaxena1",
    "linkedin": "https://www.linkedin.com/in/pratyush-saxena-735b81215/",
    "spotify": "https://open.spotify.com/user/31yu4lbmsbl5w3xdfawtcbnfrdfu?si=dd5f9a94a9d84721",
    "hook": "CS + AI student at Cornell. Most recently a security and automation intern at Cisco (Splunk). Previously at NASA, Biostate AI, and Alpheva AI.",
    "about": (
        "I'm an undergraduate at Cornell studying computer science and artificial "
        "intelligence. Besides coding, my interests include late-night drives, music "
        "(any genre), guitar, my dog Waffle, and basketball."
    ),
}

EXPERIENCE = [
    {
        "company": "Splunk (Cisco)",
        "role": "Software Security & Automation Engineering Intern",
        "dates": "Summer 2026",
        "description": (
            "I interned on the security and automation engineering side of "
            "Splunk. I built an MCP tool that normalizes freeze and scheduling data "
            "so agents can figure out maintenance time blocks across more than "
            "15,000 stacks, and I cut query latency by about 100ms on Splunk's "
            "source of truth by replacing an HTTP cache with direct Redis access in "
            "Go. I also rolled out cybersecurity and code-style standards across "
            "15+ repositories to improve the quality of AI-generated code."
        ),
        "tags": ["Go", "Redis", "MCP", "Security", "Automation"],
    },
    {
        "company": "Alpheva AI",
        "role": "Product Analytics & Engineering Intern",
        "dates": "2025 - 2026",
        "description": (
            "I worked on both the product and analytics side of a "
            "fintech app. I built a React Native Reports dashboard with cash-flow "
            "visualizations and category-level spending breakdowns that help users "
            "better understand their finances and save an average of about $6,500 "
            "per year. I also helped create investor pitch decks that were used in "
            "securing partnerships with companies like OpenAI, Google, and Amazon, "
            "and supported go-to-market efforts by analyzing competitors, making "
            "product demo videos, and reaching out to roughly 1,000 venture capital "
            "investors."
        ),
        "tags": ["React Native", "Product Analytics", "Fintech", "Data Viz", "GTM"],
    },
    {
        "company": "Biostate AI",
        "role": "AI Research Intern",
        "dates": "Fall 2025",
        "description": (
            "I worked in a human-in-the-loop machine learning research workflow, "
            "where I reviewed AI-generated analyses, validated statistical results, "
            "fixed figures, and edited LLM-generated manuscript drafts. I used "
            "CNN-based analysis and LLM tools to study immunology datasets involving "
            "CD8⁺ PD-L1⁺ immune cells in murine models. I also co-authored more than "
            "five AI-assisted research papers that were submitted to peer-reviewed "
            "journals, including Genome Biology."
        ),
        "tags": ["CNN", "LLMs", "Bioinformatics", "Research", "Python"],
    },
    {
        "company": "NASA",
        "role": "Software Engineer Intern",
        "dates": "Summer 2024",
        "description": (
            "I worked on Python software for a laser-based wireless power transfer "
            "proof-of-concept between satellites in orbit. I led a small team and "
            "focused mainly on two things: building a computer vision algorithm in "
            "OpenCV to track a laser point in real time, and writing IMU-based "
            "software to help stabilize the satellite's orientation. At the end of "
            "the internship, I presented our results, including ~98% laser-aiming "
            "accuracy, to over 100 NASA engineers and scientists."
        ),
        "tags": ["Python", "OpenCV", "Computer Vision", "IMU", "Robotics"],
    },
    {
        "company": "TJHSST Computer Systems Lab",
        "role": "Student Systems Administrator",
        "dates": "2022 - 2023",
        "description": (
            "I was selected as one of eight students to help maintain my school's IT "
            "infrastructure, including dozens of workstations, servers, and internal "
            "tools. As the Documentation Co-Lead, I wrote over 50 pages of technical "
            "documentation to make sure future students could maintain and understand "
            "the system."
        ),
        "tags": ["Linux", "Sysadmin", "Documentation"],
    },
]

PROJECTS = [
    {
        "name": "Baya",
        "subtitle": "AI-Powered Interior Design Platform",
        "description": (
            "I built an AI interior design platform that combines Claude with four "
            "fal.ai image models to turn a single photo of a room into "
            "photorealistic redesigns, chaining up to seven sequential edits while "
            "preserving the room's architecture and linking to real products you "
            "can buy. Under the hood I added cross-provider fallback (Claude "
            "Sonnet ↔ Haiku and fal.ai ↔ Replicate), distributed concurrency "
            "control with Upstash, and a pgvector product-matching system seeded "
            "from the eBay and Amazon APIs."
        ),
        "tags": ["Claude", "fal.ai", "pgvector", "Upstash", "AI"],
        "links": [{"label": "live site", "href": "https://bayacollections.com/"}],
    },
    {
        "name": "Drizzle",
        "subtitle": "Autoimmune Disorder Social Network",
        "description": (
            "I built a full-stack, cross-platform social media app for people "
            "living with autoimmune disorders using React Native and Next.js. It "
            "includes Supabase Auth with OAuth, real-time messaging, fine-grained "
            "privacy controls, push notifications, infinite-scrolling feeds, and "
            "Cloudflare R2 image uploads with cloud-backed synchronization."
        ),
        "tags": ["React Native", "Next.js", "Supabase", "Cloudflare R2"],
        "links": [{"label": "app page", "href": "https://www.joindrizzle.com/welcome"}],
    },
    {
        "name": "4Sight",
        "subtitle": "Insider Trading Monitor",
        "description": (
            "I built a Python-based tool that scrapes and parses SEC Form 4 insider "
            "trading filings using the EDGAR API, tested across 50+ tickers. On top "
            "of that, I added an NLP model that analyzes insider trades alongside "
            "global news to generate possible explanations for trading behavior."
        ),
        "tags": ["Python", "NLP", "EDGAR API", "Web Scraping", "Finance"],
        "links": [{"label": "live demo", "href": "https://4-sight-mu.vercel.app/"}],
    },
    {
        "name": "T-REX",
        "subtitle": "Tunable-Resonance Electricity eXperiment",
        "description": (
            "I helped prototype a floor tile that harvests electricity from foot "
            "traffic and ambient sound using piezoelectric crystals, reaching "
            "roughly 1.4 mW per step per dollar - over 30x more cost-efficient than "
            "competing drum-harvester designs. I also built an AI resonance-tuning "
            "system that predicts ambient vibration and sound frequencies and "
            "adjusts pressure on the crystal through a motorized brace to keep the "
            "tile near peak resonance for maximum output."
        ),
        "tags": ["Hardware", "Piezoelectrics", "AI", "Energy"],
        "links": [{"label": "CAD model", "href": "https://cad.onshape.com/documents/fd8ac6e3e5df3313a0ddd5a9/w/895eaee745abf19deca5ee34/e/9d8877913008a508a817565b?renderMode=0&uiState=6a53a814f4e375455e4e581e"}],
    },
    {
        "name": "SkIntel",
        "subtitle": "AI Skin Cancer Detection App",
        "description": (
            "Under the mentorship of an MIT PhD student, I built a convolutional "
            "neural network in Python that detects skin cancer from lesion images. "
            "The model works with smartphone-quality photos and achieved an AUC "
            "score of 0.93. My team and I presented the project to an audience of "
            "over 150 people."
        ),
        "tags": ["Python", "CNN", "Computer Vision", "Healthcare"],
        "links": [{"label": "live demo", "href": "https://skintel-o20f.onrender.com/"}],
    },
    {
        "name": "Marrow",
        "subtitle": "Scroll-to-Learn iOS App",
        "description": (
            "I built an offline iOS app that turns learning into a "
            "vertical-scrolling feed of educational cards spanning computer "
            "science, finance, math, and science. Using Expo, TypeScript, and "
            "NativeWind, I wove an SM-2 spaced-repetition scheduler invisibly "
            "into the scroll so you recall ideas you saw weeks ago, with all "
            "progress persisted on-device in SQLite. The app runs entirely "
            "offline with no backend, accounts, or network calls, shipping a "
            "hand-reviewed corpus in the app bundle."
        ),
        "tags": ["React Native", "Expo", "TypeScript", "SQLite", "iOS"],
        "links": [{"label": "app page", "href": "https://pratyushsaxena1.github.io/marrow/"}],
    },
    {
        "name": "wE-Study",
        "subtitle": "Collaborative Online Study Platform",
        "description": (
            "I designed and built a full-stack web platform that helps students "
            "organize and coordinate study sessions. I used HTML, CSS, JavaScript, "
            "and SQL, and set up a relational database with phpMyAdmin to manage "
            "users, sessions, and authentication securely."
        ),
        "tags": ["HTML", "CSS", "JavaScript", "SQL", "phpMyAdmin"],
        "links": [{"label": "live site", "href": "https://we-study.free.je/"}],
    },
]

@app.context_processor
def inject_site():
    return {"site": SITE, "now_year": datetime.utcnow().year}


# ----- landing -----
@app.route('/')
def landing():
    return render_template('landing.html')


# ----- terminal (fun) version -----
@app.route('/terminal')
def terminal_index():
    return render_template(
        'terminal/index.html',
        experience=EXPERIENCE,
        projects=PROJECTS,
    )


@app.route('/terminal/experience')
def terminal_experience():
    return render_template('terminal/experience.html', experience=EXPERIENCE)


@app.route('/terminal/projects')
def terminal_projects():
    return render_template('terminal/projects.html', projects=PROJECTS)


@app.route('/terminal/resume')
def terminal_resume():
    return render_template('terminal/resume.html')


# ----- classic version -----
@app.route('/classic')
def classic():
    return render_template(
        'classic/index.html',
        experience=EXPERIENCE,
        projects=PROJECTS,
    )


# ----- pretty resume url -----
@app.route('/resume.pdf')
def resume_file():
    return redirect(url_for('static', filename='resume.pdf'))


# AdSense ownership verification for tools.pratyushsaxena.com.
@app.route('/ads.txt')
def ads_txt():
    return ('google.com, pub-1429285815293223, DIRECT, f08c47fec0942fa0\n',
            200, {'Content-Type': 'text/plain'})


# ----- legacy redirects (keep old shared links working) -----
@app.route('/homepage')
def _legacy_homepage():
    return redirect(url_for('landing'), code=301)


@app.route('/experience')
def _legacy_experience():
    return redirect(url_for('terminal_experience'), code=301)


@app.route('/projects')
def _legacy_projects():
    return redirect(url_for('terminal_projects'), code=301)


@app.route('/resume')
def _legacy_resume():
    return redirect(url_for('terminal_resume'), code=301)


# ----- public analytics for tools.pratyushsaxena.com -----
TOOLS_ORIGIN = "https://tools.pratyushsaxena.com"


def _tools_cors(resp):
    origin = request.headers.get("Origin", "")
    # localhost is only a valid cross-origin caller during local development.
    allow_localhost = app.debug and origin.startswith("http://localhost:")
    if origin == TOOLS_ORIGIN or allow_localhost:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Max-Age"] = "86400"
    return resp


@app.route('/api/tool-visits/track', methods=['POST', 'OPTIONS'])
def tool_visits_track():
    if request.method == 'OPTIONS':
        return _tools_cors(app.make_response(('', 204)))
    # Cap how fast any one client can write analytics rows.
    if _rate_limited(f"track:{request.remote_addr or 'unknown'}", 30, 60.0):
        return _tools_cors(app.make_response((jsonify({'error': 'rate limited'}), 429)))
    slug = None
    try:
        data = request.get_json(silent=True) or {}
        slug = data.get('slug') if isinstance(data, dict) else None
    except Exception:
        slug = None
    analytics.record_tool_hit(request, slug)
    stats = analytics.tool_visit_stats()
    return _tools_cors(jsonify(stats))


@app.route('/api/tool-visits/count', methods=['GET', 'OPTIONS'])
def tool_visits_count():
    if request.method == 'OPTIONS':
        return _tools_cors(app.make_response(('', 204)))
    return _tools_cors(jsonify(analytics.tool_visit_stats()))


# ----- analytics admin -----
@app.route('/admin/report')
def admin_report():
    expected = os.environ.get('ADMIN_TOKEN')
    # Prefer the X-Admin-Token header (never lands in access logs); fall back to
    # the query param for browser convenience. Constant-time comparison.
    provided = request.headers.get('X-Admin-Token') or request.args.get('token', '')
    if not expected or not hmac.compare_digest(provided, expected):
        abort(404)
    try:
        days = int(request.args.get('days', 7))
    except (TypeError, ValueError):
        days = 7
    days = max(1, min(days, 3650))
    report = analytics.build_report(days=days)
    if request.args.get('format') == 'json':
        return jsonify(report)
    if request.args.get('email') == '1':
        ok, msg = analytics.send_email(report)
        return jsonify({'ok': ok, 'msg': msg, 'report': report})
    return analytics.render_html(report)


if __name__ == '__main__':
    # Debug is OFF unless explicitly enabled for local dev (FLASK_DEBUG=1).
    # In production the app is served by gunicorn (see Procfile), which never
    # runs this block, so the Werkzeug debugger is never exposed.
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=debug)
