import os
from flask import Flask, render_template, redirect, url_for, send_from_directory

app = Flask(__name__)

RESUME_FILENAME = "Pratyush Saxena Resume.pdf"

SITE = {
    "name": "Pratyush Saxena",
    "first_name": "Pratyush",
    "role": "CS + AI @ Cornell",
    "location": "Ithaca, NY",
    "email": "pratyushsaxena4@gmail.com",
    "github": "https://github.com/pratyushsaxena1",
    "linkedin": "https://www.linkedin.com/in/pratyush-saxena-735b81215/",
    "spotify": "https://open.spotify.com/user/31yu4lbmsbl5w3xdfawtcbnfrdfu?si=dd5f9a94a9d84721",
    "hook": "CS + AI student at Cornell. Interning at Cisco (Splunk) Summer 2026. Previously at NASA, Biostate AI, and Alpheva AI.",
    "about": (
        "I'm an undergraduate at Cornell studying computer science and artificial "
        "intelligence. Besides coding, my interests include late-night drives, music "
        "(any genre), guitar, my dog Waffle, and basketball."
    ),
}

EXPERIENCE = [
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
        "company": "Alpheva AI",
        "role": "Product Analytics & Engineering Intern",
        "dates": "2024 – 2025",
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
        "dates": "2024",
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
        "company": "TJHSST Computer Systems Lab",
        "role": "Student Systems Administrator",
        "dates": "2022 – 2023",
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
        "name": "wE-Study",
        "subtitle": "Collaborative Online Study Platform",
        "description": (
            "I designed and built a full-stack web platform that helps students "
            "organize and coordinate study sessions. I used HTML, CSS, JavaScript, "
            "and SQL, and set up a relational database with phpMyAdmin to manage "
            "users, sessions, and authentication securely."
        ),
        "tags": ["HTML", "CSS", "JavaScript", "SQL", "phpMyAdmin"],
        # TODO(pratyush): drop a real GitHub/demo URL in here when ready
        "links": [],
    },
    {
        "name": "4Sight",
        "subtitle": "Insider Trading Monitor",
        "description": (
            "I built a Python-based tool that scrapes SEC Form 4 insider trading "
            "filings using the EDGAR API. On top of that, I added an NLP model that "
            "analyzes insider trades alongside recent news to generate possible "
            "explanations for trading behavior."
        ),
        "tags": ["Python", "NLP", "EDGAR API", "Web Scraping", "Finance"],
        "links": [],
    },
    {
        "name": "T-REX",
        "subtitle": "Tunable-Resonance Electricity eXperiment",
        "description": (
            "I helped prototype a floor tile that generates electricity from "
            "mechanical and sound energy using piezoelectric materials. I also built "
            "an AI model that predicts environmental conditions and adjusts applied "
            "pressure on the tile to improve energy output."
        ),
        "tags": ["Hardware", "Piezoelectrics", "AI", "Energy"],
        "links": [],
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
        "links": [],
    },
]

@app.context_processor
def inject_site():
    return {"site": SITE}


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


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=debug)
