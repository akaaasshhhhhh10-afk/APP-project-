"""Seed corpus from report Appendix 9.1 (24 alumni) and 9.2 (5 events) plus one demo account per role."""
import json

from .db import new_id, now_iso
from .security import hash_password

DEMO_PASSWORD = "password123"

# (name, year, degree, role, company, location, skills)
ALUMNI = [
    ("Aarav Mehta", 2026, "B.Tech CS", "Product Engineer", "Microsoft", "Bengaluru", ["Python", "React", "AI"]),
    ("Diya Kapoor", 2025, "B.Tech IT", "Software Engineer", "Google", "Hyderabad", ["Java", "Cloud", "System Design"]),
    ("Kabir Shah", 2024, "B.Tech CS", "Data Scientist", "Adobe", "Mumbai", ["Python", "Machine Learning", "SQL"]),
    ("Ananya Iyer", 2023, "M.Tech DS", "ML Engineer", "NVIDIA", "Pune", ["AI", "Python", "Deep Learning"]),
    ("Vihaan Rao", 2026, "B.Tech Elec", "Frontend Engineer", "Razorpay", "Bengaluru", ["React", "TypeScript", "Design"]),
    ("Saanvi Nair", 2025, "B.Tech CS", "UX Designer", "Figma", "Remote", ["UI/UX", "Figma", "Research"]),
    ("Arjun Reddy", 2024, "B.Tech CS", "Backend Engineer", "Amazon", "Chennai", ["Java", "AWS", "System Design"]),
    ("Myra Desai", 2023, "MCA", "Cybersecurity Analyst", "Cisco", "Mumbai", ["Security", "Networking", "Python"]),
    ("Ishaan Gupta", 2026, "B.Tech CS", "Full Stack Dev", "Freshworks", "Chennai", ["Node.js", "React", "MongoDB"]),
    ("Aadhya Menon", 2025, "B.Tech Mech", "Product Manager", "Swiggy", "Bengaluru", ["Product", "Analytics", "SQL"]),
    ("Reyansh Kulkarni", 2024, "B.Tech IT", "Cloud Architect", "IBM", "Pune", ["Azure", "DevOps", "Cloud"]),
    ("Pari Chatterjee", 2023, "B.Tech CS", "iOS Developer", "Apple", "Bengaluru", ["Swift", "iOS", "UI/UX"]),
    ("Advik Joshi", 2026, "B.Tech DS", "Research Associate", "IISc", "Bengaluru", ["Python", "Research", "AI"]),
    ("Ira Bose", 2025, "B.Tech CS", "Business Analyst", "Deloitte", "Kolkata", ["Analytics", "Excel", "SQL"]),
    ("Rudra Sinha", 2024, "M.Tech CS", "Platform Engineer", "Atlassian", "Remote", ["Kubernetes", "Go", "DevOps"]),
    ("Sara Thomas", 2023, "B.Tech Biotech", "Bioinformatics Eng", "Illumina", "Hyderabad", ["Python", "Genomics", "Data"]),
    ("Atharv Bhat", 2026, "B.Tech CS", "Software Developer", "Zoho", "Chennai", ["Java", "SQL", "Web"]),
    ("Navya Pillai", 2025, "B.Des Comm", "Visual Designer", "Razorpay", "Bengaluru", ["Brand", "Figma", "Illustration"]),
    ("Dhruv Jain", 2024, "B.Tech ECE", "Embedded Engineer", "Qualcomm", "Hyderabad", ["C++", "Embedded", "IoT"]),
    ("Kiara Verma", 2023, "B.Tech CS", "Engineering Manager", "Flipkart", "Bengaluru", ["Leadership", "Architecture", "Java"]),
    ("Manav Shah", 2026, "B.Tech CS", "QA Engineer", "PhonePe", "Pune", ["Testing", "Automation", "Java"]),
    ("Tara Mukherjee", 2025, "M.Tech AI", "Applied Scientist", "Amazon", "Bengaluru", ["AI", "Python", "NLP"]),
    ("Yuvan Prasad", 2024, "B.Tech CS", "Game Developer", "Ubisoft", "Pune", ["Unity", "C#", "Game Design"]),
    ("Zoya Khan", 2023, "B.Tech IT", "Founder", "SaaS Startup", "Mumbai", ["Startups", "Product", "Fundraising"]),
]

# (title, start, end, location, kind, description, creator name)
EVENTS = [
    ("Alumni Homecoming 2026", "2026-11-14T17:00", "2026-11-14T21:00", "Main Campus, Great Hall", "Community",
     "Annual reunion bringing every cohort back to campus for an evening of talks and catching up.", "Alumni Office"),
    ("Build with AI: Demo Night", "2026-11-06T18:30", "2026-11-06T21:00", "Innovation Lab, Bengaluru", "Workshop",
     "Alumni and students demo the AI projects they have been building.", "Kabir Shah"),
    ("Careers in Product & Design", "2026-10-29T16:00", "2026-10-29T18:00", "Virtual, Alumni Connect", "Talk",
     "A panel on breaking into product and design roles.", "Saanvi Nair"),
    ("The Founders Circle", "2026-11-20T19:00", "2026-11-20T21:00", "The Foundry, Mumbai", "Networking",
     "Meet alumni founders and hear what building a startup really takes.", "Zoya Khan"),
    ("Open Source Sprint", "2026-11-28T10:00", "2026-11-28T18:00", "Engineering Block, Room 204", "Workshop",
     "A full-day sprint contributing to open-source projects with mentors on hand.", "Aarav Mehta"),
]


def seed(conn) -> None:
    if conn.execute("SELECT 1 FROM alumni_profiles LIMIT 1").fetchone():
        return

    created = now_iso()
    pwd = hash_password(DEMO_PASSWORD)
    users = {}
    for name, email, role in [
        ("Demo Student", "student@demo.com", "student"),
        ("Alumni Office", "faculty@demo.com", "faculty"),
        ("Aarav Mehta", "alumni@demo.com", "alumni"),
    ]:
        users[role] = new_id()
        conn.execute(
            "INSERT INTO users (id, name, email, password_hash, role, created_at) VALUES (?,?,?,?,?,?)",
            (users[role], name, email, pwd, role, created),
        )

    for i, (name, year, degree, role, company, location, skills) in enumerate(ALUMNI):
        linked = users["alumni"] if i == 0 else None  # the demo alumni account owns Aarav's profile
        bio = f"{role} at {company}, class of {year}. Happy to mentor students on {', '.join(skills[:2])}."
        conn.execute(
            "INSERT INTO alumni_profiles (id, user_id, name, year, degree, role, company, location, skills, bio)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (f"p{i + 1}", linked, name, year, degree, role, company, location, json.dumps(skills), bio),
        )

    for i, (title, start, end, location, kind, desc, creator) in enumerate(EVENTS):
        creator_id = users["faculty"] if creator == "Alumni Office" else None
        conn.execute(
            "INSERT INTO events (id, title, starts_at, ends_at, location, kind, description, creator_id, creator_name)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (f"e{i + 1}", title, start, end, location, kind, desc, creator_id, creator),
        )
