# Attractions Feature — Integration Notes (Student 25693742)

## Почему так, а не поверх твоей ветки

Ветка `student-2-f-b-d` сильно отстала от `main` (ссылка на это же и в отзыве
Абдуллы) — в частности, `shared/gateway/services/service_router.py` в твоей
ветке **пустой**, а `docker-compose.yml` — это заглушка на 6 строк. Мержить
её как есть нельзя. Поэтому весь пакет ниже собран поверх актуального `main`
и содержит **только** то, что реально нужно добавить/поменять. Это исключает
конфликты с остальной командой.

## Что внутри архива

```
student-25693742/
├── attractions-frontend/   # nginx, статика (index.html + css)
├── attractions-backend/    # Flask :5003, CRUD + AI recommend
└── attractions-database/   # Flask :6003, отдельный HTTP-микросервис БД

shared/
├── gateway/
│   ├── services/service_router.py   # ключ "activities" -> "attractions"
│   └── routes/gateway_routes.py     # добавлен attractions_proxy
└── frontend/
    ├── index.html    # ссылка "Attractions" вместо "Coming soon"
    └── nginx.conf     # проксирование /attractions/ -> attractions-frontend

docker-compose.yml   # три новых сервиса + volume + env для gateway
.github/workflows/student-25693742-ci.yml   # CI, как у остальных фич
```

## Как применить (шаги)

1. В своей ветке **удали** старую папку `student-2/` целиком — она заменяется
   на `student-25693742/` (конвенция именования как у всей команды:
   `student-<ID>/<feature>-frontend|backend|database`, см. registration form —
   твой Student ID `25693742`).
2. Скопируй `student-25693742/` из архива в корень репозитория.
3. Скопируй `.github/workflows/student-25693742-ci.yml`.
4. Файлы в `shared/gateway/` и `shared/frontend/` из архива — это версии от
   `main` с точечными правками (2 функции в `gateway_routes.py`, 1 строка в
   `service_router.py`, обновлённые `index.html`/`nginx.conf`). Если у кого-то
   в команде за это время появились свои правки в этих же файлах — **не
   перезаписывай слепо**, а перенеси вручную только 4 изменения:
   - `service_router.py`: ключ `"activities"` → `"attractions"`,
     `ACTIVITIES_BACKEND_URL` → `ATTRACTIONS_BACKEND_URL`,
     `http://activities-backend:5003` → `http://attractions-backend:5003`
   - `gateway_routes.py`: добавлен блок `attractions_proxy` (скопируй его
     целиком из архива — вставлен после `account_proxy`, ничего в существующих
     функциях не менял)
   - `shared/frontend/index.html`: ссылка Activities → Attractions,
     карточка "Coming soon" → "Open Attractions →"
   - `shared/frontend/nginx.conf`: добавлен блок `location /attractions/`
5. `docker-compose.yml` — либо возьми целиком из архива (это `main` +
   3 сервиса), либо вручную добавь блоки `attractions-frontend`,
   `attractions-backend`, `attractions-database`, `ATTRACTIONS_BACKEND_URL`
   в `shared-gateway.environment`, и volume `attractions-database-data`.

## Порты (без конфликтов с командой)

| Сервис               | Порт |
|-----------------------|------|
| attractions-frontend  | 3003 |
| attractions-backend   | 5003 |
| attractions-database  | 6003 |

Эти порты уже были зарезервированы под "activities" в `service_router.py`
main, никто их не занимал.

## Что исправлено относительно замечаний Абдуллы

- ✅ database — теперь настоящий Flask HTTP API (порт 6003), а не "тихий" контейнер
- ✅ backend больше не импортирует sqlite напрямую — только HTTP через `services/database_api.py`
- ✅ порт backend приведён в соответствие (5003 везде: Dockerfile EXPOSE, app.run, compose)
- ✅ frontend — отдельный сервис, обслуживается nginx на 80 (проброс 3003:80)
- ✅ убраны мёртвые Flask-роуты, которые раздавали фронтенд из backend
- ✅ Ollama указывает на `http://ollama:11434/api/generate`, модель и URL берутся из env (`OLLAMA_URL`, `OLLAMA_MODEL`)
- ✅ добавлены `/health` на всех трёх сервисах
- ✅ `DATABASE_PATH=/data/attractions.db` + named volume `attractions-database-data` — данные переживают пересборку
- ✅ инициализация БД происходит при старте контейнера (`initialise_database()` в `if __name__ == "__main__"`), а не при сборке образа
- ✅ навигация во фронтенде ведёт на реальные пути (`/`, `/account`, `/accommodation/`, `/attractions/`, `/flight/search`)
- ✅ `debug=False` везде
- ✅ `requirements.txt` у database-сервиса
- ✅ `Dockerfile` с большой буквы во всех трёх сервисах
- ✅ добавлен CI-workflow `student-25693742-ci.yml` по образцу остальных фич

## Известный баг НЕ из твоей зоны (просто предупреждение команде)

В `shared/gateway/routes/gateway_routes.py` функция `accommodation_proxy`
обрывается без `return` — Flask на этом упадёт с ошибкой на реальном запросе.
Я **не стал это чинить** внутри твоей интеграции, чтобы не создавать тебе
лишний конфликт при мерже — это зона ответственности владельца шлюза/accommodation.
Просто дай им знать.

## Как быстро проверить локально

```bash
docker compose up -d attractions-database attractions-backend attractions-frontend ollama
curl http://localhost:6003/health
curl http://localhost:5003/health
curl http://localhost:5003/api/attractions
curl http://localhost:3003/attractions/
```

(Все Flask-роуты я уже прогнал руками вне Docker — CRUD, поиск, 404, отзывы
и пересчёт рейтинга работают корректно.)
