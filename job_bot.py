import os
import sys
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CANDIDATE_PROFILE = {
    "name": "Prabhu Kumar S",
    "target_roles": [
        "data analyst", "data scientist", "analytics engineer", 
        "business intelligence", "bi developer", "python developer"
    ],
    "skills": [
        "python", "sql", "postgresql", "mysql", "pandas", "numpy", 
        "tableau", "power bi", "machine learning", "scikit-learn", 
        "etl", "eda", "data pipelines", "regression", "classification"
    ]
}

SENIOR_TERMS = [
    "senior", "sr.", "sr ", "lead", "principal", "manager", "director", 
    "head of", "architect", "staff", "vp", "chief", "10+ years", "8+ years", "7+ years", "5+ years"
]

SPAM_TERMS = [
    "ai trainer", "generalist ai", "annotation", "annotator",
    "part-time", "hourly", "earn $", "earn €", "commission only",
    "survey", "clickworker", "freelance writer", "transcriptionist",
    "virtual assistant", "data entry clerk", "typing", "easy money", "unpaid"
]

def calculate_resume_match(title: str, desc: str = ""):
    text = f"{title} {desc}".lower()
    if any(spam in text for spam in SPAM_TERMS) or any(sen in text for sen in SENIOR_TERMS):
        return None, []
        
    matched = [s.upper() for s in CANDIDATE_PROFILE["skills"] if s in text]
    role_match = any(r in text for r in CANDIDATE_PROFILE["target_roles"])
    
    if not role_match and len(matched) < 2:
        return None, []
        
    score = min(98, (72 if role_match else 60) + (len(matched) * 7))
    return score, matched

def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Warning: Missing credentials.")
        print(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true"
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"User-Agent": "JobBot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print("Telegram delivered status:", resp.getcode())
    except Exception as e:
        print("Failed to deliver Telegram message:", e)

def fetch_rss_jobs(url, source, work_mode):
    jobs = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            root = ET.fromstring(resp.read())
            for item in root.findall(".//item")[:25]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                desc = item.findtext("description", "").strip()
                score, matched = calculate_resume_match(title, desc)
                if score and score >= 70:
                    clean_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    jobs.append({
                        "title": clean_title,
                        "link": link,
                        "source": source,
                        "score": score,
                        "matched": matched,
                        "mode": work_mode
                    })
    except Exception as e:
        print(f"Error {url}: {e}")
    return jobs

def fetch_remoteok():
    jobs = []
    try:
        url = "https://remoteok.com/api?tag=data"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data[1:35]:
                pos = item.get("position", "")
                comp = item.get("company", "")
                link = item.get("url", "")
                loc = item.get("location", "")
                desc = item.get("description", "")
                
                score, matched = calculate_resume_match(pos, desc)
                if score and score >= 70 and link:
                    clean_title = f"{comp}: {pos}".replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    mode = "Remote" if "remote" in (loc or "").lower() or not loc else f"Hybrid / Onsite ({loc})"
                    jobs.append({
                        "title": clean_title,
                        "link": link,
                        "source": "RemoteOK Tech",
                        "score": score,
                        "matched": matched,
                        "mode": mode
                    })
    except Exception as e:
        print(f"Error RemoteOK: {e}")
    return jobs

def fetch_all():
    all_jobs = []
    all_jobs.extend(fetch_rss_jobs("https://himalayas.app/jobs/rss?q=data", "Himalayas", "Remote"))
    all_jobs.extend(fetch_rss_jobs("https://weworkremotely.com/categories/remote-programming-jobs.rss", "WeWorkRemotely", "Remote"))
    all_jobs.extend(fetch_remoteok())

    seen = set()
    unique = []
    for j in all_jobs:
        if j["link"] not in seen:
            seen.add(j["link"])
            unique.append(j)

    unique.sort(key=lambda x: x["score"], reverse=True)
    return unique[:8]

def main():
    jobs = fetch_all()

    portals = (
        "<b>Direct Search Portals (Matched for Prabhu Kumar S):</b>\n"
        "• <a href='https://cutshort.io/search/jobs?q=data%20analyst&amp;experienceLevel=0-2'>Cutshort: Remote &amp; Bengaluru Startups</a>\n"
        "• <a href='https://www.naukri.com/data-analyst-jobs-in-bangalore-bengaluru?experience=0'>Naukri: Full-Time Corporate / Hybrid</a>\n"
        "• <a href='https://wellfound.com/jobs?role=data-analyst&amp;experience=0-2'>Wellfound: 100% Remote-First Roles</a>\n"
        "• <a href='https://www.linkedin.com/jobs/search/?keywords=Data%20Analyst&amp;f_E=2&amp;location=India'>LinkedIn: All India Roles</a>\n\n"
    )

    header = (
        "🎯 <b>Daily Job Matches Tailored for Your Resume</b>\n"
        "👤 <b>Candidate:</b> Prabhu Kumar S (Great Lakes PGP-DSE)\n"
        "🛠️ <b>Core Skills:</b> Python • SQL • Tableau • Power BI • Machine Learning\n"
        "🌐 <b>Coverage:</b> 100% Remote, Hybrid &amp; Full-Time India\n\n"
    )

    if not jobs:
        msg = f"{header}{portals}No new openings above 70% ATS score right now. Check the direct portals above!"
    else:
        msg = f"{header}{portals}<b>Top Openings (Sorted by ATS Resume Match):</b>\n\n"
        for i, j in enumerate(jobs, 1):
            skills_str = ", ".join(j["matched"][:4]) if j["matched"] else "Python, SQL"
            msg += (
                f"{i}. <b>{j['title']}</b>\n"
                f"   ⚡ <b>ATS Match:</b> {j['score']}% | 📍 <b>Mode:</b> {j['mode']}\n"
                f"   🏷️ <b>Skills:</b> {skills_str}\n"
                f"   🏢 Source: {j['source']}\n"
                f"   👉 <a href='{j['link']}'>Apply on Official Site</a>\n\n"
            )

    send_telegram_message(msg)
    print(f"Sent {len(jobs)} resume-matched multi-mode jobs successfully.")

if __name__ == "__main__":
    main()
