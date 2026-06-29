# План развития проекта — OmniScan Platform

Документ описывает переход от текущего одностраничного сканера к **многомодульной платформе** с входом по логину/паролю, ролевой моделью, админкой и меню выбора модулей. Сканер становится одним из модулей.

---

## 1. Текущее состояние (отправная точка)

- **Фронтенд:** статические `index.html` + `style.css` + `app.js` (vanilla), библиотеки с CDN (`html5-qrcode`, `lucide`).
- **Бэкенд:** `server.py` — `http.server` из stdlib, отдаёт статику и проксирует `/api/proxy` → 1С (Basic Auth из `.env`).
- **Хранилище:** нет БД; история сканов в `localStorage`.
- **Аутентификации/ролей нет.** Прокси к 1С открыт для всех в сети — это закрывается авторизацией.
- **Деплой:** dev5 (`/home/lan/web-mut`), запуск под pm2 (`omniscan`), ручной `scp`.

---

## 2. Целевая архитектура

| Слой | Технология | Примечание |
|------|-----------|-----------|
| Фронтенд | **Vue 3 + Vite** (SPA) | Роутинг `vue-router`, состояние `pinia`. Собирается в статику. |
| Бэкенд | **FastAPI** (uvicorn) | REST API + раздача собранного SPA. Прокси к 1С переносится в роут. |
| БД | **SQLite** (файл) | Через SQLAlchemy 2.x + Alembic (миграции). Один файл, бэкап копированием. |
| Аутентификация | **Сессии + httpOnly cookie** | Сессия в БД/таблице, cookie `SameSite=Lax`, `Secure`, `HttpOnly`. |
| Пароли | **passlib + bcrypt** (или argon2) | Хранятся только хеши. |
| Деплой | pm2 → `uvicorn` | SPA собирается (`vite build`) и отдаётся FastAPI same-origin (нужно для cookie). |

**Ключевой принцип:** SPA и API живут на одном origin (FastAPI отдаёт `dist/`), поэтому cookie-сессии работают без CORS-сложностей.

### Целевая структура репозитория
```
web-mut/
├── backend/
│   ├── main.py              # точка входа FastAPI
│   ├── config.py            # настройки из .env
│   ├── db.py                # сессия SQLAlchemy, engine
│   ├── models/              # User, Role, Permission, Session, Module
│   ├── schemas/             # Pydantic-схемы
│   ├── auth/                # логин, сессии, зависимости (get_current_user)
│   ├── routers/
│   │   ├── auth.py          # /api/auth/login, /logout, /me
│   │   ├── admin_users.py   # CRUD пользователей
│   │   ├── admin_roles.py   # CRUD ролей и прав
│   │   └── scanner.py       # перенос /api/proxy → 1С (модуль scanner)
│   ├── alembic/             # миграции
│   └── seed.py              # создание первого админа и базовых ролей
├── frontend/
│   ├── src/
│   │   ├── router/          # маршруты + guard по правам
│   │   ├── stores/          # auth, modules
│   │   ├── views/
│   │   │   ├── LoginView.vue
│   │   │   ├── DashboardView.vue   # меню модулей
│   │   │   ├── ScannerView.vue     # текущий сканер, портирован
│   │   │   └── admin/              # UsersView, RolesView
│   │   ├── modules/         # реестр модулей (см. §6)
│   │   └── components/
│   ├── index.html
│   └── vite.config.js
├── data/app.db              # SQLite (в .gitignore)
└── plan.md
```

---

## 3. Ролевая модель (RBAC)

Модель «пользователи → роли → права». Право — это строковый ключ (permission). Доступ к модулю и к функциям админки выражается правами.

### Сущности
- **User** — `id, username, password_hash, full_name, is_active, created_at`.
- **Role** — `id, key, name, description`. Примеры: `admin`, `manager`, `scanner_operator`.
- **Permission** — `key, description`. Делятся на:
  - доступ к модулям: `module:scanner`, `module:<other>` …
  - админские: `admin:users`, `admin:roles`.
- **user_roles** — связь M:N (пользователь может иметь несколько ролей).
- **role_permissions** — связь M:N (роль → набор прав).
- **Module** — реестр модулей (`key, name, icon, route, permission`). Может быть в БД или в коде (см. §6); по умолчанию — в коде, в БД дублируется только при необходимости динамического управления.

### Базовые роли (сидируются)
| Роль | Права |
|------|-------|
| `admin` | все права, включая `admin:users`, `admin:roles`, все `module:*` |
| `scanner_operator` | `module:scanner` |

### Принцип проверки
- **Бэкенд — источник истины.** Каждый защищённый эндпоинт требует право через зависимость FastAPI (`require_permission("module:scanner")`).
- **Фронтенд** скрывает/показывает пункты меню по правам из `/api/auth/me`, но это лишь UX — реальная защита на сервере.

---

## 4. Вход в систему (аутентификация)

### Поток
1. `POST /api/auth/login {username, password}` → проверка хеша → создание записи сессии → установка httpOnly-cookie `session_id`.
2. Все запросы шлют cookie автоматически; зависимость `get_current_user` валидирует сессию.
3. `POST /api/auth/logout` → удаление сессии и cookie.
4. `GET /api/auth/me` → текущий пользователь + роли + плоский список прав + доступные модули (для построения меню).

### Безопасность
- Пароли — bcrypt/argon2, никогда в открытом виде.
- Cookie: `HttpOnly`, `SameSite=Lax`, `Secure` (под HTTPS).
- **CSRF:** при cookie-сессиях нужна защита для изменяющих запросов — double-submit CSRF-токен или проверка `Origin`/`Referer`. Заложить в §8.
- Срок жизни сессии + продление; разлогин на сервере (инвалидация записи).
- Rate-limit на `/login` против перебора.

---

## 5. Админка (управление пользователями и ролями)

Доступна только при правах `admin:users` / `admin:roles`. Маршруты фронта под guard, API под зависимостями.

### Пользователи (`admin:users`)
- Список, поиск, пагинация.
- Создание: username, ФИО, временный пароль, набор ролей.
- Редактирование: ФИО, активность, сброс пароля, изменение ролей.
- Блокировка/деактивация (мягкое удаление через `is_active`).

API:
```
GET    /api/admin/users
POST   /api/admin/users
GET    /api/admin/users/{id}
PATCH  /api/admin/users/{id}
POST   /api/admin/users/{id}/reset-password
DELETE /api/admin/users/{id}        # деактивация
```

### Роли (`admin:roles`)
- Список ролей, создание/редактирование, назначение набора прав (чекбоксы по доступным permission, включая `module:*`).
- Защита: нельзя удалить роль `admin` / снять у себя последние админские права (предохранитель).

API:
```
GET    /api/admin/roles
POST   /api/admin/roles
PATCH  /api/admin/roles/{id}
DELETE /api/admin/roles/{id}
GET    /api/admin/permissions        # справочник доступных прав/модулей
```

---

## 6. Меню модулей

После входа пользователь попадает на **дашборд с плитками модулей**. Показываются только модули, на которые есть право.

### Реестр модулей (во фронте, `src/modules/registry.js`)
```js
export const MODULES = [
  {
    key: 'scanner',
    name: 'Сканер 1С',
    icon: 'qr-code',
    route: '/modules/scanner',
    permission: 'module:scanner',
  },
  // будущие модули добавляются сюда
];
```
- Дашборд фильтрует `MODULES` по правам пользователя (`/api/auth/me`).
- `vue-router` навешивает guard: нет права → редирект на дашборд/403.
- Бэкенд независимо защищает API каждого модуля.

### Модуль «Сканер» (портирование текущего функционала)
- `ScannerView.vue` = текущий `app.js`/`index.html`, разбитый на компоненты (камера, результат, карточка 1С, история).
- `/api/proxy` → `/api/modules/scanner/lookup?barcode=...`, теперь **за авторизацией** (закрывает дыру открытого прокси к 1С).
- История сканов: оставить в `localStorage` на первом этапе; опционально перенести в БD (per-user) позже.

---

## 7. План работ по этапам

### Этап 0 — Каркас (инфраструктура)
- Завести `backend/` (FastAPI, SQLAlchemy, Alembic) и `frontend/` (Vite + Vue 3).
- FastAPI отдаёт собранный SPA + `/api/health`.
- pm2 переключить на `uvicorn`; обновить деплой (сборка фронта).

### Этап 1 — Аутентификация
- Модели User/Session, хеширование, логин/логаут/me, cookie-сессии.
- `seed.py`: первый админ (логин/временный пароль из `.env`).
- `LoginView`, auth-store, router-guard «не залогинен → /login».

### Этап 2 — Ролевая модель
- Модели Role/Permission, связи, сидирование базовых ролей и прав.
- Зависимости `require_permission` на бэке.

### Этап 3 — Админка
- API и экраны для пользователей и ролей.
- Предохранители (последний админ, роль admin).

### Этап 4 — Меню модулей + перенос сканера
- Дашборд с плитками по правам.
- Портирование сканера в `ScannerView`, прокси 1С за авторизацией с правом `module:scanner`.

### Этап 5 — Закалка (security/ops)
- CSRF, rate-limit, флаги cookie под HTTPS, аудит-лог входов.
- Бэкап SQLite, `pm2 startup` (автозапуск при перезагрузке — см. ниже).
- Перенос секретов 1С, ротация засвеченного пароля.

---

## 8. Вопросы безопасности и эксплуатации

- **Открытый прокси 1С** — закрывается авторизацией (Этап 4).
- **Секреты:** `ONEC_AUTH` и секрет сессий — только в `.env` (уже в `.gitignore`). Засвеченный пароль 1С желательно сменить.
- **CSRF** для cookie-сессий — обязателен на изменяющих запросах.
- **HTTPS:** для `Secure`-cookie нужен TLS (reverse-proxy, напр. Caddy) — сейчас порт 3000 открыт по HTTP.
- **Автозапуск pm2** при перезагрузке сервера ещё не настроен:
  ```bash
  sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u lan --hp /home/lan
  ```
- **Миграции БД** через Alembic; `data/app.db` — в `.gitignore`, регулярный бэкап.
- **Деплой** меняется: теперь есть шаг сборки фронта (`vite build`) перед `scp`/перезапуском.

---

## 9. Открытые вопросы (уточнить перед стартом)

1. Регистрация пользователей — **только через админку** (предполагается) или нужна самостоятельная?
2. Нужен ли сброс пароля по email / обязательная смена временного пароля при первом входе?
3. Иерархия ролей или плоский набор прав (сейчас заложен плоский — проще)?
4. История сканов: оставить локальной или хранить per-user в БД (общий журнал, отчёты)?
5. Какие модули планируются после сканера — влияет на структуру меню и прав.
6. Нужна ли мультиарендность (несколько складов/организаций) или один контур?

---

> Следующий шаг: подтвердить открытые вопросы (§9) и начать с **Этапа 0** — каркас backend/frontend, после чего поэтапно наращивать функционал.

---

## 10. Запуск (реализованный каркас)

Каркас платформы реализован: бэкенд (`backend/`) и SPA (`frontend/`). Этапы 0–4 + CSRF/seed готовы.

### Backend (dev)
```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # заполнить SESSION_SECRET, ADMIN_*, ONEC_AUTH
backend/.venv/bin/python -m uvicorn backend.main:app --port 8100 --reload
```
БД (`data/app.db`) создаётся и сидируется автоматически при старте: каталог прав, роли `admin` и `scanner_operator`, первый админ из `ADMIN_*`.

### Frontend (dev)
```bash
cd frontend && npm install
npm run dev        # http://localhost:5173, проксирует /api -> :8100
```

### Production
```bash
cd frontend && npm run build        # -> frontend/dist
backend/.venv/bin/python -m uvicorn backend.main:app --port 8100
```
FastAPI отдаёт собранный `dist/` same-origin (cookie-сессии работают без CORS).

> ⚠️ Сборка фронта на macOS с library-validation падает на native-модулях rollup/esbuild
> («different Team IDs»). Сборку выполнять на Linux (dev5: `node 20`) — `dist` статичен и
> переносится как есть.

### Что проверено e2e (локально, Playwright)
- Вход admin → дашборд с плиткой модуля; выход.
- Админка: создание пользователя `operator2` с ролью `scanner_operator`.
- RBAC: оператор видит только модуль сканера; `/admin/*` → редирект на `/forbidden`;
  API `/api/admin/users` → 403, `/api/modules/scanner/lookup` → 200.
- CSRF: POST без заголовка `X-CSRF-Token` → 403.
- Прокси 1С работает за авторизацией.

### Осталось (не входило в каркас)
- Alembic-миграции (сейчас `create_all` при старте).
- Деплой на dev5 и решение о выводе на порт 3000 вместо текущего сканера (**cutover —
  согласовать**), pm2-юнит для uvicorn, HTTPS для `Secure`-cookie.
- Открытые вопросы §9.
