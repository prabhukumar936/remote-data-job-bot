import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

KEYWORDS = [
    "data analyst",
    "data scientist",
    "analytics engineer",
    "business intelligence",
    "bi engineer",
    "power bi",
    "tableau",
    "python",
    "sql",
    "etl",
    "machine learning",
]


def send_telegram_message(message: str):
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Warning: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
    print("Dry run output:\n", message)
    return

  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = urllib.parse.urlencode({
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "HTML",
      "disable_web_page_preview": "true",
  }).encode("utf-8")

  req = urllib.request.Request(
      url, data=payload, headers={"User-Agent": "JobBot/1.0"}
  )
  try:
    with urllib.request.urlopen(req, timeout=15) as resp:
      print("Telegram delivered status:", resp.getcode())
  except Exception as e:
    print("Failed to deliver Telegram message:", e)


def fetch_rss_jobs(url):
  jobs = []
  try:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        },
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
      xml_data = resp.read()
      root = ET.fromstring(xml_data)
      for item in root.findall(".//item")[:25]:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        title_lower = title.lower()
        if any(kw in title_lower for kw in KEYWORDS):
          jobs.append({"title": title, "link": link})
  except Exception as e:
    print(f"Error reading {url}: {e}")
  return jobs


def fetch_remoteok_api():
  jobs = []
  try:
    url = "https://remoteok.com/api?tag=data"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        },
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
      data = json.loads(resp.read().decode("utf-8"))
      for item in data[1:20]:
        position = item.get("position", "")
        company = item.get("company", "")
        apply_url = item.get("url", "")
        if position and apply_url:
          title = f"{company}: {position}"
          jobs.append({"title": title, "link": apply_url})
  except Exception as e:
    print(f"Error fetching RemoteOK API: {e}")
  return jobs


def fetch_all_jobs():
  all_jobs = []
  all_jobs.extend(fetch_rss_jobs("https://himalayas.app/jobs/rss?q=data"))
  all_jobs.extend(
      fetch_rss_jobs(
          "https://weworkremotely.com/categories/remote-programming-jobs.rss"
      )
  )
  all_jobs.extend(fetch_remoteok_api())

  seen = set()
  unique = []
  for j in all_jobs:
    if j["link"] not in seen:
      seen.add(j["link"])
      unique.append(j)
  return unique[:10]


def main():
  jobs = fetch_all_jobs()
  if not jobs:
    msg = (
        "🎯 <b>Daily Remote Job Bot</b>\n\nNo new matching remote data roles"
        " found today. Will check again tomorrow!"
    )
  else:
    msg = (
        f"🎯 <b>Daily Remote Data Analyst / Scientist Jobs ({len(jobs)} Fresh"
        " Roles)</b>\n\n"
    )
    for i, j in enumerate(jobs, 1):
      msg += (
          f"{i}. <b>{j['title']}</b>\n👉 <a href='{j['link']}'>Apply"
          " Here</a>\n\n"
      )

  send_telegram_message(msg)
  print(f"Processed {len(jobs)} jobs successfully.")


if __name__ == "__main__":
  main()
