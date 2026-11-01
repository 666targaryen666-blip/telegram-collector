# Короткий звіт: Telegram Collector

**Джерело.** Публічні Telegram-канали, доступні через офіційний Telegram MTProto API (бібліотека Telethon). Канали налаштовуються через `CHANNELS` у `.env`. Приватні чати та групи не збираються. Авторизація здійснюється власними `api_id`/`api_hash` та захищеною сесією.

**Дані та модель.** Записи зберігаються в SQLite у спільній таблиці `messages` з полями `author`, `url`, `date`, `text`, а також `source`, `message_id`, `media_type`, `collected_at`. URL повідомлення є канонічним посиланням `https://t.me/<channel>/<id>`. Для відтворюваності реалізовано експорт у JSONL і CSV. Вкладення не завантажуються; зберігається лише тип медіа. Публічний username каналу виступає полем `author`.

**Інкрементність і стійкість.** Для кожного каналу окремо ведеться `last_id`. Наступний прогін бере лише нові повідомлення; транзакція атомарно фіксує повідомлення та курсор. Окремий `backfill_before_id` дозволяє поступово добирати історію без повторного повного обходу. Дублікати відкидаються за `(source,message_id)` і `url`. Помилки ізолюються по каналах і записуються в журнал `runs`.

**Ліміти.** Реалізовано обмеження розміру партії, затримку між запитами та обробку Telegram `FloodWaitError` з фіксацією тривалості очікування. На відміну від HTTP API, MTProto не використовує заголовки `Retry-After`/`X-RateLimit-*`; релевантний сигнал — кількість секунд у FloodWait. Реальні значення лімітів і статистика FloodWait можуть бути наведені лише після запуску з власними обліковими даними. Ротація акаунтів для обходу лімітів не використовується.

**Перевірка та результат.** До архіву додано 200 **синтетичних** демонстраційних JSONL-записів для перевірки формату, а не 200 реально зібраних публікацій. Для завершення емпіричної частини домашнього завдання потрібно виконати `collect`/`backfill`, експортувати щонайменше 200 реальних повідомлень і доповнити звіт фактичними цифрами запусків та FloodWait. Перед здачею перевірити правила використання та приватність даних.
Real Telegram Data Collection — Results

Data source

- Platform: Telegram
- Public channel: "NOELREPORTS" (https://t.me/noel_reports)
- Collection method: Public Telegram web preview ("https://t.me/s/noel_reports")
- API credentials: Not required for this collection method

Collection results

Metric| Result
Pages processed| 13
Real text messages collected| 200
Unique message URLs| 200
Records with empty text| 0
Records without a date| 0
Records without an author| 0

Data storage

The collected messages were saved in two formats:

- JSONL: "data/noel_reports_real.jsonl"
- SQLite: "data/noel_reports.sqlite"

Each message contains the source, message ID, author, URL, publication date, and text.

Deduplication

Messages are identified using their source, message ID, and unique URL.

The first SQLite import inserted 200 messages. Repeating the import inserted 0 additional messages, confirming that duplicate records are ignored.

Rate-limit handling

The public web collector uses randomized delays of 3–6 seconds between requests and stops when Telegram responds with HTTP 429.

Dashboard

The Streamlit dashboard was connected to the SQLite database and successfully displayed the 200 collected messages.

Limitations

- The collector currently saves text messages; media-only posts are skipped.
- The public Telegram HTML structure may change.
- The web collection script supports pagination and basic duplicate prevention, but persistent pagination cursors and automatic resumption from the last collected page are not yet implemented.
- The data represents messages from one public channel and should not be considered representative of Telegram as a whole.

Conclusion

The project successfully collected, validated, and stored 200 real Telegram text messages. The results were verified using JSONL checks, SQLite queries, a repeated import, and the Streamlit dashboard.