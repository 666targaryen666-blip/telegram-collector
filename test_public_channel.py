import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://t.me/s/noel_reports"

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; TelegramCollectorHomework/1.0)"
}

print("Завантажуємо сторінку NOELREPORTS...")

try:
    response = requests.get(URL, headers=headers, timeout=20)
    response.raise_for_status()
except requests.RequestException as error:
    print("Помилка завантаження:", error)
    raise SystemExit(1)

soup = BeautifulSoup(response.text, "html.parser")

messages = soup.select(".tgme_widget_message")

print("HTTP статус:", response.status_code)
print("Знайдено повідомлень:", len(messages))
print("-" * 50)

for message in messages[:3]:
    post_id = message.get("data-post", "")

    text_element = message.select_one(".tgme_widget_message_text")
    date_element = message.select_one("time[datetime]")

    text = text_element.get_text(" ", strip=True) if text_element else ""
    date = date_element.get("datetime", "") if date_element else ""

    url = f"https://t.me/{post_id}" if post_id else ""

    print("URL:", url)
    print("Дата:", date)
    print("Текст:", text[:250])
    print("-" * 50)
    # Перевіряємо посилання на старіші повідомлення
older_link = soup.select_one("a.tme_messages_more")

print("\nПеревірка переходу до старіших повідомлень:")

if older_link:
    print("Знайдено посилання:", older_link.get("href"))
else:
    print("Посилання на старіші повідомлення не знайдено.")
    from urllib.parse import urljoin

if older_link:
    older_url = urljoin(URL, older_link.get("href"))

    print("\nЗавантажуємо старіші повідомлення...")
    print("Адреса:", older_url)

    try:
        older_response = requests.get(
            older_url,
            headers=headers,
            timeout=20
        )
        older_response.raise_for_status()

        older_soup = BeautifulSoup(
            older_response.text,
            "html.parser"
        )

        older_messages = older_soup.select(
            ".tgme_widget_message"
        )

        print("HTTP статус:", older_response.status_code)
        print("Знайдено старіших повідомлень:", len(older_messages))

        print("\nПерші 3 повідомлення другої сторінки:")

        for message in older_messages[:3]:
            post_id = message.get("data-post", "")
            print("https://t.me/" + post_id)

    except requests.RequestException as error:
        print("Помилка завантаження:", error)