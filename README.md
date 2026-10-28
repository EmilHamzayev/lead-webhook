# Lead webhook

Невеликий сервіс на FastAPI: приймає заявку через HTTP webhook, перевіряє її, відсікає дублікати за `external_id`, визначає категорію, надсилає повідомлення в Telegram і зберігає заявку зі статусом у SQLite.

## Запуск локально (Windows / macOS / Linux)

Потрібен Python 3.11+.

```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

pytest                       # тести
uvicorn app.main:app --reload
```

Сервіс: http://127.0.0.1:8000, документація Swagger: http://127.0.0.1:8000/docs

## Запуск у Docker

```bash
docker build -t lead-webhook .
docker run --rm -p 8000:8000 --env-file .env -v lead-data:/data lead-webhook
```

## Змінні середовища

| Змінна | Опис |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота від @BotFather |
| `TELEGRAM_CHAT_ID` | Куди надсилати повідомлення |
| `DATABASE_PATH` | Шлях до файлу SQLite (за замовчуванням `leads.db`) |

Якщо токен або chat id не задані, сервіс працює в **dry-run** режимі: повідомлення лише пишеться в лог. Так проєкт можна запустити без реального бота. Шаблон: `.env.example`.

## API

`POST /webhook/lead`

```bash
curl -X POST http://127.0.0.1:8000/webhook/lead \
  -H "Content-Type: application/json" \
  -d '{"external_id":"lead-1001","name":"Anna","message":"Хочу записатися на процедуру наступного тижня","source":"instagram"}'
```

| Ситуація | Код | Відповідь |
|---|---|---|
| Нова заявка, Telegram OK | 201 | `{"status": "sent", "duplicate": false, ...}` |
| Нова заявка, Telegram недоступний | 201 | `{"status": "failed", "duplicate": false, ...}` |
| Повтор `external_id` | 200 | `{"status": <поточний статус>, "duplicate": true, ...}` |
| Невалідні дані | 422 | опис помилок валідації |

Також: `GET /leads/{external_id}` (заявка зі статусом і помилкою), `GET /health`.

## Основні рішення

- **Дублікати** відсікаються обмеженням `UNIQUE(external_id)` і `INSERT ... ON CONFLICT DO NOTHING`. Перевірка й вставка виконуються однією атомарною операцією, тому два одночасні запити з одним `external_id` не оброблюються двічі (на відміну від «SELECT, потім INSERT»).
- **Порядок: спершу зберегти, потім надіслати.** Якщо Telegram недоступний, заявка не губиться: вона лишається в БД зі статусом `failed` і текстом помилки.
- **Помилка Telegram не повертає 5xx.** Заявку вже прийнято. 5xx спричинив би повтори з боку відправника, які все одно відсіклися б як дублікати.
- **Категорія** визначається простими правилами за ключовими словами (`app/categorizer.py`): `complaint` > `booking` > `price` > `other`. Інтерфейс `categorize(text) -> str` дозволяє замінити правила на LLM без змін в іншому коді.
- **Безпека:** користувацькі дані екрануються для `parse_mode=HTML`. Токен бота не потрапляє в текст помилок і в БД. Таймаут запиту до Telegram 5 с.
- **Тестованість:** `create_app(db_path, sender)` отримує залежності ззовні, тому тести використовують тимчасову БД і фейковий sender, а HTTP до Telegram мокається через `httpx.MockTransport`.

## Структура

```
app/
  schemas.py      валідація вхідних даних (Pydantic)
  categorizer.py  визначення категорії
  telegram.py     форматування й надсилання повідомлення
  db.py           SQLite: схема, вставка без дублікатів, статуси
  api.py          FastAPI-ендпоінти (фабрика застосунку)
  main.py         збирання застосунку зі змінних середовища
tests/            31 тест (pytest)
```

## Що я додав би в production-версії

- Повторне надсилання `failed` заявок (фонова черга / ретраї з backoff) замість синхронної відправки в запиті.
- Перевірку автентичності webhook (секретний заголовок або HMAC-підпис).
- PostgreSQL і міграції (Alembic) замість SQLite.
- Структуровані логи, метрики та алерти на зростання `failed`.
- Rate limiting і обмеження розміру тіла запиту.
- CI (тести + лінтер) і закріплені версії залежностей через lock-файл.

## Використання AI-інструментів

Claude Code використовувався для генерації коду, тестів і README. Я перевіряв кожен крок, запускав тести після кожної частини логіки й розібрав прийняті рішення.

## Витрачений час

15 хвилин
