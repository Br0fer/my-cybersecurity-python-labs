import json
import sqlite3
from contextlib import closing
from pathlib import Path

from labs.lab_3.database import get_connection, initialize_database

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"
EXPECTED_CATEGORIES = 3
EXPECTED_RECORDS = 8


def load_seed(path: Path = SEED_PATH) -> dict:
    """Прочитати seed.json і перевірити його структуру"""
    data = json.loads(path.read_text(encoding="utf-8"))
    categories = data.get("categories")
    records = data.get("records")
    if not isinstance(categories, list) or len(categories) != EXPECTED_CATEGORIES:
        raise ValueError(f"Очікувалось категорій: {EXPECTED_CATEGORIES}")
    if not isinstance(records, list) or len(records) != EXPECTED_RECORDS:
        raise ValueError(f"Очікувалось записів: {EXPECTED_RECORDS}")

    return data


def is_database_empty(connection: sqlite3.Connection) -> bool:
    """Перевірити, що в обох таблицях немає записів"""
    categories = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    records = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    return categories == 0 and records == 0


def seed_database() -> None:
    """Заповнити порожню базу даних даними з seed.json"""
    try:
        data = load_seed()
    except (OSError, ValueError) as e:
        print(f"Некоректні початкові дані: {e}")
        return

    initialize_database()
    with closing(get_connection()) as connection:
        if not is_database_empty(connection):
            print("База вже містить дані, заповнення пропущено.")
            return
        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(c["id"], c["name"]) for c in data["categories"]],
                )
                connection.executemany(
                    "INSERT INTO records (code, title, category_id, value, status) VALUES (?, ?, ?, ?, ?)",
                    [
                        (
                            r["code"],
                            r["title"],
                            r["category_id"],
                            r["value"],
                            r["status"],
                        )
                        for r in data["records"]
                    ],
                )

        except (sqlite3.Error, KeyError) as e:
            print(f"Помилка при заповненні бази даних: {e}")
            return
    print("Початкове заповнення виконано успішно: 3 категорії та 8 записів")


if __name__ == "__main__":
    seed_database()
