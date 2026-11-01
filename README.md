# Telegram Collector

Python-проєкт для збору повідомлень із публічних Telegram-каналів. Підтримує вебзбір без API-ключів та альтернативний збір через Telethon. Дані зберігаються у JSONL і SQLite, реалізовано захист від дублікатів, інкрементний збір, тести та Streamlit-дашборд. Додатково передбачені backfill і Docker для API-колектора.

## 1. Підготовка

Для вебзбору потрібен Python та встановлені залежності. Telegram API-ключі не потрібні. Для альтернативного збору через Telethon необхідні Telegram-акаунт, api_id та api_hash. Отримайте `api_id` і `api_hash` на https://my.telegram.org. Не публікуйте їх або файли `.session`.

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
```

Впишіть у `.env` `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`; змініть `CHANNELS` на публічні канали, з яких дозволено збирати публікації. Для Docker встановіть `TELEGRAM_SESSION=/app/sessions/collector_session`. Перший запуск попросить номер телефону, код підтвердження та, за потреби, 2FA пароль. Нікому їх не передавайте.

## 2. Команди

```bash
python -m collector.main collect --limit 100
python -m collector.main backfill --limit 100
python -m collector.main export --output data/messages.jsonl
python -m collector.main export --output data/messages.csv
streamlit run dashboard.py
pytest -q
```

`collect` читає лише повідомлення з `id > last_id` у хронологічному порядку, максимум `--limit` на канал. Курсор оновлюється **разом із записами в одній транзакції**. `backfill` запускайте після першого `collect`: він читає старіші записи пачками та веде окремий `backfill_before_id`. Повторні запуски не створюють дублікати завдяки `PRIMARY KEY (source,message_id)` і `UNIQUE(url)`. Для 200+ реальних записів запускайте backfill кілька разів (залежить від історії каналів), після чого експортуйте JSONL.

**Увага:** файл `data/demo_200.jsonl` — синтетичні демонстраційні дані, а **не** фактично зібрані повідомлення. Для здачі реальних даних замініть його експортом після запуску API-колектора та перевірте кількість записів.

## 3. Ліміти та помилки

`REQUEST_DELAY_SECONDS` задає паузу між каналами та Telethon `wait_time` для ітерації; `BATCH_SIZE` обмежує розмір прогону. Telethon обробляє транспортні retry; `FloodWaitError` записується в таблицю `runs`, запити до відповідного каналу припиняються до наступного запуску. Не використовуйте зміну акаунтів/проксі для обходу FloodWait. Telegram MTProto не надає звичайних HTTP 429 / `Retry-After` заголовків: аналог — `FloodWaitError.seconds`. При помилці одного каналу решта обробляються.

## 4. Docker

```bash
docker compose build
docker compose run --rm collector
# після авторизації:
docker compose up dashboard
```

Dashboard: http://localhost:8501. Сесія зберігається в `./sessions/`, дані — в `./data/`. Якщо контейнеру не вистачає інтерактивного термінала, виконайте першу авторизацію локально й використовуйте власний session-файл у захищеному volume.

## 5. Модель

`messages(source, message_id, author, url, date, text, media_type, collected_at)`. `author` = публічний username каналу (не приватний автор), `date` = ISO 8601 UTC. Медіафайли не завантажуються, зберігається лише тип вкладення. Службові таблиці `cursors` та `runs`. JSONL/CSV експортує канонічні поля та службові ідентифікатори.

## 6. Етика

Збирайте лише загальнодоступні канали, дотримуйтеся умов Telegram, авторських прав та приватності. Не збирайте приватні чати й не обходьте обмеження. За потреби видаляйте персональні дані перед публікацією датасету.

## 7. Обмеження

У цьому архіві немає реальних API-ключів і не виконувалась Telegram-авторизація; тому реальний збір потребує запуску користувачем. Проксі SOCKS4/5/HTTP опційний через `PROXY_URL`, для мережевої сумісності, не обходу лімітів. Ротацію акаунтів навмисно не реалізовано, щоб не обходити антиаб'юз механізми.

## 8. Збір реальних Telegram-повідомлень без API

Проєкт підтримує збір повідомлень із публічних Telegram-каналів через вебперегляд Telegram без використання API-ключів.

Джерело: "@noel_reports" (https://t.me/noel_reports)
Вебсторінка: https://t.me/s/noel_reports
Результат: 253 реальні текстові повідомлення.

Збір реалізовано у файлі "collect_public.py". Скрипт переглядає публічні сторінки Telegram, переходить до старіших повідомлень і зберігає нові записи без дублювання вже зібраних.

Запуск на Windows

Для запуску використовується Python 3.13.

Створення віртуального середовища:

py -3.13 -m venv .venv313

Встановлення залежностей:

.\.venv313\Scripts\python.exe -m pip install -r requirements.txt

Збір повідомлень:

.\.venv313\Scripts\python.exe collect_public.py

Імпорт повідомлень у SQLite:

.\.venv313\Scripts\python.exe import_real.py

Запуск автоматичних тестів:

.\.venv313\Scripts\python.exe -m pytest -q

Результати

Показник| Значення
Реальні текстові повідомлення| 253
Записи в SQLite| 253
Нові записи під час повторного імпорту| 0
Успішні автоматичні тести| 2

Файли даних

- "data/noel_reports_real.jsonl" — 253 реальні повідомлення, збережені у форматі JSONL.
- "data/noel_reports.sqlite" — локальна база SQLite, яка не завантажується на GitHub.
- "data/demo_200.jsonl" — синтетичні демонстраційні дані, які не враховуються як реальні повідомлення.

Базу SQLite можна створити з файлу реальних повідомлень, запустивши "import_real.py".

Dashboard

Для перегляду даних використовується Streamlit.

У файлі ".env" можна вказати:

DATABASE_PATH=data/noel_reports.sqlite

Запуск:

.\.venv313\Scripts\python.exe -m streamlit run dashboard.py

Після запуску відкрийте http://localhost:8501.

Альтернативний збір через Telethon

У проєкті також є колектор на основі Telethon, який використовує Telegram API. Для нього потрібні власні "api_id" і "api_hash".

Однак 253 реальні повідомлення, наведені у звіті, зібрано вебколектором без API-ключів.

Обмеження

Вебколектор збирає повідомлення, що містять текст. Публікації лише з медіафайлами пропускаються. Доступність публічних сторінок і структура HTML Telegram можуть змінюватися.

Докладні результати роботи описані у файлі "report.md".