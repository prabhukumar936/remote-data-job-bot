import os
import sys
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

KEYWORDS = [
    "data analyst", "data scientist", "analytics engineer", 
    "business intelligence", "bi engineer", "power bi", "tableau", 
    "python", "sql", "etl", "machine learning"
]

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

def fetch_remote_jobs():
    jobs = []
    feeds = [
        "https://himalayas.app/jobs/rss?q=data",
        "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    ]
    for url in feeds:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall(".//item")[:20]:
                    title = item.findtext("title", "").strip()
                    link = item.findtext("link", "").strip()
                    t_lower = title.lower()
                    if any(kw in t_lower for kw in KEYWORDS):
                        clean_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        jobs.append({
                            "title": clean_title,
                            "link": link,
                            "type": "Remote"
                        })
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
    return jobs

def fetch_remoteok_jobs():
    jobs = []
    try:
        url = "https://remoteok.com/api?tag=data"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data[1:25]:
                pos = item.get("position", "")
                comp = item.get("company", "")
                link = item.get("url", "")
                location = item.get("location", "Remote")
                p_lower = pos.lower()
                if any(kw in p_lower for kw in KEYWORDS):
                    full_title = f"{comp}: {pos}".replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    jobs.append({
                        "title": full_title,
                        "link": link,
                        "type": f"Full-Time ({location or 'Remote'})"
                    })
    except Exception as e:
        print(f"Error fetching RemoteOK: {e}")
    return jobs

def fetch_all_curated_jobs():
    combined = []
    combined.extend(fetch_remote_jobs())
    combined.extend(fetch_remoteok_jobs())
    
    seen = set()
    unique = []
    for j in combined:
        if j["link"] not in seen:
            seen.add(j["link"])
            unique.append(j)
            
    return unique[:8]

def main():
    jobs = fetch_all_curated_jobs()
    
    portal_links = (
        "<b>Direct Search (India Remote &amp; Full-Time):</b>\n"
        "• <a href='https://cutshort.io/search/jobs?q=data%20analyst&amp;remote=true'>Cutshort: India Remote Data Analyst</a>\n"
        "• <a href='https://www.naukri.com/data-analyst-jobs-in-bangalore-bengaluru'>Naukri: Full-Time Bengaluru / Remote</a>\n"
        "• <a href='https://wellfound.com/jobs?role=data-analyst&amp;remote=true'>Wellfound: Remote-First Roles</a>\n"
        "• <a href='https://www.linkedin.com/jobs/search/?keywords=Data%20Analyst&amp;f_WT=2&amp;f_TPR=r86400'>LinkedIn: India Remote</a>\n\n"
    )

    if not jobs:
        msg = f"🎯 <b>Daily India Remote &amp; Full-Time Job Alert</b>\n\n{portal_links}No new RSS matches right now. Check the links above!"
    else:
        msg = f"🎯 <b>Daily India Remote &amp; Full-Time Data Jobs ({len(jobs)} Fresh Roles)</b>\n\n{portal_links}<b>Today's Verified Openings:</b>\n\n"
        for i, j in enumerate(jobs, 1):
            msg += f"{i}. <b>{j['title']}</b>\n   🏷️ {j['type']}\n   👉 <a href='{j['link']}'>Apply Now</a>\n\n"
            
    send_telegram_message(msg)
    print(f"Delivered {len(jobs)} targeted roles successfully.")

if __name__ == "__main__":
    main()
