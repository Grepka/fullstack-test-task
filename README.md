# File Exchange MVP

## Оригинальное задание вынесено в TASK.md

## Выявленые проблемы

service.py смешивает DB, storage, HTTP и бизнес-логику;
upload читает файл целиком в память;  
worker дублирует DB setup;  
service слой кидает HTTPException;  
delete может конфликтовать с alerts;  
Docker Postgres port выглядит подозрительно;
Redis env name не совпадает с кодом.

## Что сделано

Пока черновик.

## Backend architecture

Пока черновик.

## Запуск

```bash
docker compose -f docker-compose.dev.yml up --build
docker exec -it backend alembic upgrade head
