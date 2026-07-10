# File Exchange MVP

MVP файлообменника: пользователь загружает файл, backend сохраняет его, Celery worker проверяет файл на подозрительные признаки, извлекает metadata и создает alert.

Оригинальная постановка задания вынесена в [TASK.md](TASK.md). В решении сохранена исходная бизнес-логика, но backend переработан архитектурно, исправлены проблемы запуска и обработки файлов, добавлены базовые проверки.

## Бизнес-логика

После upload система выполняет тот же сценарий:

1. Создает запись о файле со статусом `uploaded`.
2. Запускает фоновую обработку.
3. Проверяет файл на подозрительные признаки: опасное расширение, размер больше 10 MB, mismatch PDF extension/MIME type.
4. Записывает результат scan: `clean` или `suspicious`.
5. Извлекает metadata: расширение, размер, MIME type, text statistics или примерное число страниц PDF.
6. Завершает обработку статусом `processed` или `failed`.
7. Создает alert: `info`, `warning` или `critical`.

## Что изменено

### Backend architecture

- `app.py` оставлен точкой сборки FastAPI-приложения.
- HTTP endpoints вынесены в `api/`.
- Бизнес-сценарии вынесены в `services/`.
- SQLAlchemy-запросы изолированы в `repositories/`.
- Настройки и DB session setup вынесены в `config.py` и `database.py`.
- Работа с файловой системой вынесена в `storage.py`.
- Celery entrypoints оставлены в `tasks.py`, а pipeline-логика вынесена в `worker/`.
- HTTP-ошибки убраны из бизнес-логики и заменены доменными исключениями.

```text
backend/src/
  api/             FastAPI роутеры
  services/        бизнес-сценарии
  repositories/    запросы к базе данных
  worker/          реализация Celery pipeline
  config.py        настройки из переменных окружения
  database.py      SQLAlchemy async engine/session
  exceptions.py    доменные ошибки
  storage.py       работа с файловым хранилищем
  tasks.py         точки входа Celery-задач
```

### Reliability fixes

- Upload больше не читает весь файл в память.
- При ошибке создания записи в БД загруженный файл удаляется с диска.
- При удалении файла сначала удаляются связанные alerts и запись в БД, затем файл на диске.
- Alert creation сделан идемпотентным, чтобы повторный запуск worker-задачи не создавал дубли.
- Metadata extraction errors переводят файл в `failed` и приводят к `critical` alert.
- Подсчет PDF pages больше не считает `/Pages` как обычную страницу.
- Docker-конфигурация приведена к рабочему виду: Postgres внутри сети на `5432`, backend/worker зависят от Redis.
- Добавлен `GET /health` для проверки backend и доступности БД.

## Неочевидная оптимизация

Главная оптимизация - потоковая работа с upload-файлом.

В исходном варианте backend вызывал `await upload_file.read()` и держал весь файл в памяти перед записью на диск. Теперь файл пишется chunk-by-chunk, поэтому расход памяти не растет пропорционально размеру файла. Это особенно важно для файлообменника: даже простой MVP не должен блокировать процесс большим upload.

Дополнительно обработка файла в Celery разделена на небольшие понятные шаги (`scan`, `metadata extraction`, `alert`), но общая логика вынесена из task wrappers в worker/services helpers. Это снижает дублирование и упрощает обработку ошибок.

## Запуск

```bash
docker compose -f docker-compose.dev.yml up --build
```

В отдельном терминале применить миграции:

```bash
docker exec -it backend alembic upgrade head
```

Frontend:

```text
http://localhost:3000/test
```

Backend docs:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

## Smoke check

Обычный файл:

```bash
curl -F "title=Readme smoke" -F "file=@README.md" http://localhost:8000/files
```

Подозрительный файл:

```bash
printf "test\n" > /tmp/suspicious.sh
curl -F "title=Suspicious smoke" -F "file=@/tmp/suspicious.sh" http://localhost:8000/files
```

Проверить результат обработки:

```bash
curl http://localhost:8000/files
curl http://localhost:8000/alerts
curl http://localhost:8000/health
```

Ожидаемое поведение:

- обычный файл получает `scan_status: clean` и `info` alert;
- `.sh` файл получает `scan_status: suspicious` и `warning` alert;
- при ошибке обработки файл получает `processing_status: failed` и `critical` alert.

## Проверки

Backend unit tests:

```bash
docker exec -it backend python -m unittest discover -s tests
```

Docker config:

```bash
docker compose -f docker-compose.dev.yml config
```
