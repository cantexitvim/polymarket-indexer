# Polymarket Indexer

Backend-приложение для индексации токеновых переводов в сети Polygon и расчёта балансов кошельков, связанных с Polymarket.

Сервис получает события из смарт-контрактов через RPC, сохраняет историю переводов в PostgreSQL и предоставляет REST API для получения актуальных балансов.

## Features

- Индексация событий `Transfer`, `TransferSingle` и `TransferBatch` из смарт-контрактов.
- Обработка входящих и исходящих переводов токенов.
- Расчёт балансов на основе истории переводов.
- Инкрементальное сканирование блокчейна с сохранением последнего обработанного блока.
- Асинхронное взаимодействие с блокчейном и PostgreSQL.
- REST API для получения информации о кошельке и его балансах.

## Tech Stack

- **Python 3.12+**
- **FastAPI** — REST API
- **Web3.py** — взаимодействие со смарт-контрактами Polygon
- **PostgreSQL** — хранение кошельков, переводов и балансов
- **SQLAlchemy 2.0** — асинхронная работа с базой данных
- **Alembic** — миграции схемы БД
- **Pydantic Settings** — конфигурация приложения
- **Docker Compose** — запуск приложения и базы данных
- **Poetry** — управление зависимостями

## Architecture

Проект разделён на компоненты, отвечающие за API, бизнес-логику, взаимодействие с блокчейном и хранение данных.

- **API** — обработка HTTP-запросов через FastAPI.
- **Service** — управление процессом индексации и расчётом балансов.
- **Blockchain** — получение событий смарт-контрактов через Web3.py.
- **Repository** — запросы к PostgreSQL через SQLAlchemy.
- **Database Models** — модели кошельков, переводов и балансов.

## Database

Основные сущности:

- `wallets` — адреса кошельков и последний обработанный блок.
- `token_transfers` — история переводов с данными о токене, сумме, транзакции и контрагенте.
- `wallet_balances` — агрегированные балансы токенов по кошелькам.

История переводов используется для расчёта изменений баланса. Ограничения уникальности предотвращают повторное сохранение одних и тех же событий.

## Installation

### Requirements

- Python 3.12+
- Poetry
- Docker и Docker Compose
- RPC endpoint для сети Polygon

### Configuration

Клонируйте репозиторий и перейдите в его директорию:

```bash
git clone https://github.com/cantexitvim/polymarket-indexer.git
cd polymarket-indexer
```

Создайте `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Настройте переменные окружения:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:postgres_password@localhost:5432/polymarket_indexer
RPC_URL=https://rpc.ankr.com/polygon/YOUR_API_KEY
ABI_PATH=abi/abis.json
SHOW_DOCS=True
DEBUG=False
```

Укажите действующий RPC endpoint с доступом к сети Polygon.

### Запуск через Docker Compose

Запустите приложение и PostgreSQL:

```bash
docker compose up --build
```

При старте контейнера приложения автоматически выполняются миграции Alembic, после чего запускается FastAPI.

API будет доступно по адресу `http://localhost:8000`.

## API

### Get wallet balance

```http
GET /api/balance?wallet_address={address}
```

Возвращает информацию о кошельке и список его балансов. Если кошелёк ещё не индексировался, сервис создаёт запись и обрабатывает доступные события начиная с начального блока сканирования.

Пример запроса:

```bash
curl "http://localhost:8000/api/balance?wallet_address=0xYOUR_WALLET_ADDRESS"
```

При включённой документации интерактивная спецификация доступна по адресу `http://localhost:8000/docs`.

## Project Structure

```text
polymarket-indexer/
├── abi/
│   └── abis.json
├── alembic/
│   └── versions/
├── app/
│   ├── core/
│   ├── database/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── session.py
│   ├── schemas/
│   ├── api.py
│   ├── blockchain.py
│   ├── services.py
│   └── main.py
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── poetry.lock
```
