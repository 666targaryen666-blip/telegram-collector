import json
import random
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CHANNEL = "noel_reports"
START_URL = f"https://t.me/s/{CHANNEL}"
OUTPUT = Path("data/noel_reports_real.jsonl")
TARGET = 260
MAX_PAGES = 40

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; TelegramCollectorHomework/1.0)"
}

session = requests.Session()
session.headers.update(headers)

records = {}

# Підхоплюємо попередні результати, якщо файл уже існує.
if OUTPUT.exists():
    for line in OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            records[record["url"]] = record
last_saved_id = max(
    (int(record["message_id"]) for record in records.values()),
    default=0,
)

print(f"Уже збережено повідомлень: {len(records)}")
print(f"Останній збережений ID: {last_saved_id}")            

url = START_URL
visited_pages = set()

for page in range(1, MAX_PAGES + 1):
    if len(records) >= TARGET:
        break

    if url in visited_pages:
        print("Сторінка повторилася. Зупиняємося.")
        break

    visited_pages.add(url)
    print(f"\nСторінка {page}: {url}")

    try:
        response = session.get(url, timeout=20)

        if response.status_code == 429:
            print("Telegram обмежив запити (HTTP 429). Зупиняємося.")
            break

        response.raise_for_status()

    except requests.RequestException as error:
        print("Помилка:", error)
        break

    soup = BeautifulSoup(response.text, "html.parser")
    messages = soup.select(".tgme_widget_message")

    if not messages:
        print("Повідомлень немає. Зупиняємося.")
        break

    added = 0
    newer_found = 0
    reached_saved_messages = False

    for message in messages:
        post_id = message.get("data-post", "")
        text_element = message.select_one(".tgme_widget_message_text")
        date_element = message.select_one("time[datetime]")

        if not post_id or not date_element:
            continue

        text = (
            text_element.get_text(" ", strip=True)
            if text_element
            else ""
        )

        # Поки пропускаємо повідомлення без тексту.
        if not text:
            continue

        message_url = f"https://t.me/{post_id}"
        message_id = int(post_id.rsplit("/", 1)[-1])

        if last_saved_id > 0 and message_id <= last_saved_id:
            reached_saved_messages = True
            continue

        if message_url in records:
            continue

        if message_id > last_saved_id:
            newer_found += 1

        records[message_url] = {
            "source": CHANNEL,
            "message_id": message_id,
            "author": CHANNEL,
            "url": message_url,
            "date": date_element["datetime"],
            "text": text,
            "media_type": None,
        }

        added += 1

        if len(records) >= TARGET:
            break

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as file:
        for record in records.values():
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Додано: {added}")
    print(f"Нових за ID повідомлень на цій сторінці: {newer_found}")
    print(f"Усього унікальних текстових повідомлень: {len(records)}")

    if reached_saved_messages:
        print("Досягнуто раніше збережених повідомлень. Зупиняємо збір.")
        break

    if len(records) >= TARGET:
        break

    older_link = soup.select_one("a.tme_messages_more")

    if not older_link or not older_link.get("href"):
        print("Старіших сторінок більше немає.")
        break

    next_url = urljoin(url, older_link["href"])

    if next_url == url:
        break

    url = next_url

    delay = random.uniform(3, 6)
    print(f"Пауза {delay:.1f} секунди...")
    time.sleep(delay)

print(f"\nГотово. Збережено {len(records)} записів.")
print(f"Файл: {OUTPUT}")
