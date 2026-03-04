# DataRoom API

REST API backend for **DataRoom** — a file and folder management application. Provides folders, file uploads (PDF), favorites, soft delete (trash), restore, and search.

## Tech Stack

- **Python 3.12+**
- **FastAPI** — web framework
- **SQLAlchemy 2** (async) + **asyncpg** — PostgreSQL
- **Pydantic** / **pydantic-settings** — config and request/response schemas
- **Alembic** — migrations
- **Uvicorn** — ASGI server
- **aiofiles** — async file I/O for uploads

## Prerequisites

- **Python 3.12+**
- **PostgreSQL** (running and reachable)
- **uv** or **pip** for dependencies

The **DataRoom Web** frontend expects this API at `http://localhost:8000` in development (with `/api` proxied to it).

## Getting Started

### Create virtual environment and install dependencies

```bash
# with uv
uv sync

# or with pip
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

### Environment variables

Create a `.env` file in the project root (see **Environment Variables** below). At minimum set `POSTGRES_URL` for the database.

### Run database migrations

```bash
alembic upgrade head
```

### Run development server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at **http://localhost:8000**. Interactive docs: **http://localhost:8000/docs**.

### Run production server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Adjust workers and binding as needed (e.g. with **gunicorn** + uvicorn workers).

## Environment Variables

| Variable           | Description                                      | Default                    |
|--------------------|--------------------------------------------------|----------------------------|
| `POSTGRES_URL`     | Async PostgreSQL URL (e.g. `postgresql+asyncpg://user:pass@localhost/db`) | — (required) |
| `STORAGE_PATH`     | Directory for uploaded PDF files                 | `./data/storage`            |
| `ALLOWED_ORIGINS`  | CORS origins, comma-separated                    | `http://localhost:5173`    |

Create a `.env` file in the project root; `pydantic-settings` loads it automatically.

## Main Features

- **Folders** — create, list (root and by id), get one with subfolders and files, breadcrumb path, rename, toggle favorite, delete (cascade soft-delete of files, then hard delete folder)
- **Files** — list (root or by folder), upload PDFs (multipart), download, rename, toggle favorite, soft delete, restore from trash
- **Search** — full-text search by name (`/search?query=...`), favorites list (`/search/favorites`), trash list (`/search/trash`)

## Project Structure (overview)

```
dataroom-api/
├── main.py                 # FastAPI app, CORS, router mount at /api/v1
├── app/
│   ├── api/
│   │   ├── router.py       # Aggregates routes
│   │   ├── dependencies.py # DB session dependency
│   │   └── routes/
│   │       ├── folders.py  # Folder CRUD, path, favorite
│   │       ├── files.py    # File CRUD, upload, download, restore
│   │       └── search.py   # Search, favorites, trash
│   ├── core/
│   │   ├── config.py       # Settings (env)
│   │   └── database.py     # Async engine and session
│   ├── models/             # SQLAlchemy models (Folder, File)
│   └── schemas/            # Pydantic request/response
├── alembic/                # Migrations
├── scripts/                # e.g. check_db
└── data/storage/           # Uploaded files (created from STORAGE_PATH)
```

## API Base and Routes

All endpoints are under **`/api/v1`**.

| Method | Path                        | Description                    |
|--------|-----------------------------|--------------------------------|
| POST   | `/folders`                  | Create folder                  |
| GET    | `/folders`                  | List root folders              |
| GET    | `/folders/{id}`             | Get folder with subfolders and files |
| GET    | `/folders/{id}/path`        | Breadcrumb path                |
| PATCH  | `/folders/{id}`             | Rename folder                  |
| PATCH  | `/folders/{id}/favorite`    | Toggle favorite                |
| DELETE | `/folders/{id}`             | Delete folder (and contents)   |
| GET    | `/files`                    | List files (optional `folder_id`) |
| POST   | `/files/upload`             | Upload PDF(s)                  |
| GET    | `/files/{id}/download`      | Download file                  |
| PATCH  | `/files/{id}`               | Rename file                    |
| PATCH  | `/files/{id}/favorite`      | Toggle favorite                |
| DELETE | `/files/{id}`               | Soft delete (move to trash)    |
| POST   | `/files/{id}/restore`       | Restore from trash             |
| GET    | `/search`                   | Search by name (`query`)       |
| GET    | `/search/favorites`         | Favorites                      |
| GET    | `/search/trash`             | Trash list                     |

See **http://localhost:8000/docs** for request/response schemas and examples.
