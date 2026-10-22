import sqlite3
from contextlib import closing

from labs.lab_3.database import get_connection

SELECT_RECORD = """
SELECT r.id, r.code, r.title, r.category_id,
       c.name AS category_name, r.value, r.status
FROM records AS r
JOIN categories AS c ON c.id = r.category_id
"""


class CategoryNotFoundError(Exception):
    """Категорії з вказаним id не існує."""

    def __init__(self, category_id: int) -> None:
        super().__init__(category_id)
        self.category_id = category_id


def _open() -> sqlite3.Connection:
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def get_record(record_id: int) -> dict | None:
    with closing(_open()) as connection:
        row = connection.execute(
            SELECT_RECORD + " WHERE r.id = ?",
            (record_id,),
        ).fetchone()
    return dict(row) if row else None


def create_record(
    code: str, title: str, category_id: int, value: float, status: str
) -> dict:
    """Додати запис і повернути його разом з category_name."""
    with closing(_open()) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO records (code, title, category_id, value, status) VALUES (?, ?, ?, ?, ?)",
            (code, title, category_id, value, status),
        )
        record_id = cursor.lastrowid

    if record_id is None:
        raise RuntimeError("Не вдалося отримати id створеного запису")
    record = get_record(record_id)
    if record is None:
        raise RuntimeError("Створений запис не знайдено")
    return record


def delete_record(record_id: int) -> bool:
    with closing(_open()) as connection, connection:
        cursor = connection.execute(
            "DELETE FROM records WHERE id = ?",
            (record_id,),
        )
    return cursor.rowcount > 0


def create_category(name: str) -> dict:
    with closing(_open()) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO categories (name) VALUES (?)",
            (name,),
        )
        category_id = cursor.lastrowid

    return {"id": category_id, "name": name}


def list_categories() -> list[dict]:
    with closing(_open()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()

    return [dict(row) for row in rows]


def delete_category(category_id: int) -> bool:
    with closing(_open()) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM categories WHERE id = ?",
                (category_id,),
            )
        return cursor.rowcount > 0


def replace_record(
    record_id: int, code: str, title: str, category_id: int, value: float, status: str
) -> dict | None:
    with closing(_open()) as connection, connection:
        cursor = connection.execute(
            "UPDATE records SET code = ?, title = ?, category_id = ?, value = ?, status = ? WHERE id = ?",
            (code, title, category_id, value, status, record_id),
        )
        if cursor.rowcount == 0:
            return None

    return get_record(record_id)


def list_records(
    category_id: int | None,
    status: str | None,
    min_value: float | None,
    q: str | None,
    limit: int,
    offset: int,
) -> list[dict]:
    conditions: list[str] = []
    params: list = []

    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    query = SELECT_RECORD
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY r.id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(_open()) as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def create_records_bulk(records: list[dict]) -> list[dict]:
    created_ids: list[int] = []

    with closing(_open()) as connection:
        with connection:
            for item in records:
                category = connection.execute(
                    "SELECT 1 FROM categories WHERE id = ?",
                    (item["category_id"],),
                ).fetchone()
                if category is None:
                    raise CategoryNotFoundError(item["category_id"])

                cursor = connection.execute(
                    "INSERT INTO records (code, title, category_id, value, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        item["code"],
                        item["title"],
                        item["category_id"],
                        item["value"],
                        item["status"],
                    ),
                )
                created_ids.append(cursor.lastrowid)

        placeholders = ", ".join("?" * len(created_ids))
        rows = connection.execute(
            SELECT_RECORD + f" WHERE r.id IN ({placeholders}) ORDER BY r.id",
            created_ids,
        ).fetchall()

    return [dict(row) for row in rows]
