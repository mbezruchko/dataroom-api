# API Endpoints Specification: Data Room MVP

**Base URL:** `/api/v1`

## 📂 Папки (Folders)

### 1. Получение содержимого директории
`GET /folders/{folder_id}`
* **Параметры:** `folder_id` (пусто для корневой директории).
* **Логика:** Возвращает список подпапок и файлов, где `is_deleted = false`.
* **Response:** `{ "id": 1, "name": "Finance", "breadcrumbs": [...], "subfolders": [...], "files": [...] }`

### 2. Создание папки
`POST /folders`
* **Body:** `{ "name": "New Folder", "parent_id": 123 }`
* **Логика:** Создает запись в БД. Если `parent_id` не указан, папка считается корневой.

### 3. Переименование папки
`PATCH /folders/{folder_id}`
* **Body:** `{ "name": "Updated Name" }`

### 4. Избранное (Toggle Favorite)
`PATCH /folders/{folder_id}/favorite`
* **Body:** `{ "is_favorite": true/false }`
* **Логика:** Меняет флаг `is_favorite` для быстрого доступа.

### 5. Удаление папки
`DELETE /folders/{folder_id}`
* **Логика:** Рекурсивно помечает все файлы внутри этой папки (и подпапок) как `is_deleted = true`. Сама папка удаляется из БД (или тоже помечается, если нужен Soft Delete для папок).

---

## 📄 Файлы (Files)

### 1. Загрузка файла
`POST /files/upload`
* **Content-Type:** `multipart/form-data`
* **Params:** `folder_id` (обязательно).
* **Validation:** Проверка расширения `.pdf` (согласно ТЗ).
* **Логика:** Сохраняет файл в `/storage/{uuid}.pdf`, записывает метаданные и `size` в БД.

### 2. Переименование файла
`PATCH /files/{file_id}`
* **Body:** `{ "name": "new_report_name.pdf" }`
* **Логика:** Обновляет поле `name` и `updated_at`. Физический путь в хранилище остается прежним.

### 3. Мягкое удаление файла (Soft Delete)
`DELETE /files/{file_id}`
* **Логика:** Устанавливает `is_deleted = true`. Файл перестает отображаться в списках, но остается на диске и в БД.

### 4. Скачивание/Просмотр файла
`GET /files/{file_id}/download`
* **Response:** `FileResponse` (стриминг PDF файла).

---

## 🔍 Дополнительно (Extra Credit)

### 1. Поиск
`GET /search?query=report`
* **Логика:** Глобальный поиск по именам файлов и папок среди тех, что не удалены.

### 2. Статус (SSE)
`GET /events/upload-progress/{task_id}`
* **Type:** `text/event-stream`
* **Логика:** Трансляция статуса обработки файла на фронтенд.