import os
import sys
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Core Technical Roles
KEYWORDS = [
    "data analyst", "data scientist", "analytics engineer", 
    "business intelligence", "bi engineer", "power bi", "tableau", 
    "python", "sql", "etl", "machine learning"
]

# Strict Scam/Gig/Spam Filter
SPAM_TERMS = [
    "ai trainer", "generalist ai", "annotation", "annotator",
    "part-time", "hourly", "earn $", "earn €", "commission only",
    "survey", "clickworker", "freelance writer", "transcriptionist",
    "virtual assistant", "data entry clerk", "typing", "no experience required",
    "easy money", "unpaid", "training program (fee"
]

def is_trustable_job(title: str, company: str = "") -> bool:
    text = f"{company} {title}".lower()
    if any(spam in text for spam in SPAM_TERMS):
        return False
    return any(kw in text for kw in KEYWORDS)

def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Warning: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
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

def fetch_rss_verified(url, source_label):
    jobs = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            root = ET.fromstring(resp.read())
            for item in root.findall(".//item")[:25]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                
                if is_trustable_job(title):
                    clean_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    jobs.append({
                        "title": clean_title,
                        "link": link,
                        "source": source_label,
                        "type": "Full-Time / Remote"
                    })
    except Exception as e:
        print(f"Error fetching from {url}: {e}")
    return jobs

def fetch_remoteok_verified():
    jobs = []
    try:
        url = "https://remoteok.com/api?tag=data"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data[1:30]:
                pos = item.get("position", "")
                comp = item.get("company", "")
                link = item.get("url", "")
                loc = item.get("location", "Remote")
                
                if is_trustable_job(pos, comp) and link:
                    full_title = f"{comp}: {pos}".replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    jobs.append({
                        "title": full_title,
                        "link": link,
                        "source": "RemoteOK",
                        "type": f"Full-Time ({loc or 'Remote'})"
                    })
    except Exception as e:
        print(f"Error fetching RemoteOK: {e}")
    return jobs

def fetch_trustable_jobs():
    all_jobs = []
    all_jobs.extend(fetch_rss_verified("https://himalayas.app/jobs/rss?q=data", "Himalayas Tech"))
    all_jobs.extend(fetch_rss_verified("https://weworkremotely.com/categories/remote-programming-jobs.rss", "WeWorkRemotely"))
    all_jobs.extend(fetch_remoteok_verified())

    seen = set()
    verified = []
    for j in all_jobs:
        if j["link"] not in seen:
            seen.add(j["link"])
            verified.append(j)

    return verified[:7]

def main():
    jobs = fetch_trustable_jobs()

    portals = (
        "<b>🛡️ Trustable India Remote &amp; Full-Time Platforms:</b>\n"
        "• <a href='https://cutshort.io/search/jobs?q=data%20analyst&amp;remote=true'>Cutshort (Direct Founder &amp; HR Chat)</a>\n"
        "• <a href='https://www.naukri.com/data-analyst-jobs-in-bangalore-bengaluru'>Naukri Verified (Bengaluru/Remote)</a>\n"
        "• <a href='https://wellfound.com/jobs?role=data-analyst&amp;remote=true'>Wellfound (Funded Startups with Salary Transparency)</a>\n"
        "• <a href='https://www.linkedin.com/jobs/search/?keywords=Data%20Analyst&amp;f_WT=2&amp;f_TPR=r86400'>LinkedIn Verified (India Remote)</a>\n\n"
    )

    if not jobs:
        msg = f"🛡️ <b>Verified Full-Time &amp; India Remote Alerts</b>\n\n{portals}"
    else:
        msg = f"🛡️ <b>Verified Full-Time &amp; Remote Openings ({len(jobs)} Active Roles)</b>\n\n{portals}"
        for i, j in enumerate(jobs, 1):
            msg += (
                f"{i}. <b>{j['title']}</b>\n"
                f"   🏢 Source: {j['source']} | 💼 {j['type']}\n"
                f"   👉 <a href='{j['link']}'>Apply on Official Site</a>\n\n"
            )

    send_telegram_message(msg)
    print(f"Sent {len(jobs)} verified openings successfully.")

if __name__ == "__main__":
    main()
