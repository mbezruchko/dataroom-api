# Database Schema: Data Room MVP

## Описание архитектуры
Система использует **PostgreSQL** для хранения метаданных. Файлы физически хранятся в локальной директории сервера, а в БД записывается путь к ним. Реализован механизм **Soft Delete** для файлов и расширенные атрибуты для папок.

---

### 1. Таблица `folders`
Хранит иерархическую структуру директорий.

| Поле | Тип | Описание |
| :--- | :--- | :--- |
| `id` | UUID / Integer | Первичный ключ. |
| `name` | String(255) | Название папки. |
| `parent_id` | Integer (FK) | Ссылка на `folders.id`. NULL для корневых папок. |
| `is_favorite` | Boolean | Флаг "Избранное". По умолчанию `false`. |
| `created_at` | DateTime | Время создания (server_default: now()). |

**Особенности:**
* Рекурсивная связь `parent_id` позволяет создавать неограниченную вложенность.
* При удалении папки через API, дочерние элементы должны обрабатываться согласно логике бизнес-правил (в данном ТЗ — рекурсивное удаление или пометка).

---

### 2. Таблица `files`
Хранит метаданные загруженных PDF-документов.

| Поле | Тип | Описание |
| :--- | :--- | :--- |
| `id` | UUID / Integer | Первичный ключ. |
| `name` | String(255) | Оригинальное имя файла. |
| `storage_path` | Text | Путь к файлу в файловой системе сервера. |
| `size` | BigInteger | Размер файла в байтах. |
| `folder_id` | Integer (FK) | Ссылка на `folders.id`. |
| `is_deleted` | Boolean | Флаг мягкого удаления. По умолчанию `false`. |
| `created_at` | DateTime | Время первой загрузки. |
| `updated_at` | DateTime | Время последнего изменения (переименования). |

**Особенности:**
* **Soft Delete:** Поле `is_deleted` используется для исключения файлов из обычных выборок без физического удаления с диска.
* **Авто-обновление:** `updated_at` обновляется автоматически при выполнении `UPDATE`.

---

### 3. Индексы и Оптимизация
* **Index** на `parent_id` в таблице `folders` для быстрого получения содержимого директории.
* **Index** на `folder_id` и `is_deleted` в таблице `files` для ускорения фильтрации активных файлов в папке.
* **Unique Constraint** на пару `(name, parent_id)` в папках и `(name, folder_id)` в файлах (опционально, для предотвращения дубликатов в одной директории).

---

### 4. SQL DDL (Справочно)
```sql
CREATE TABLE folders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    size BIGINT,
    folder_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);