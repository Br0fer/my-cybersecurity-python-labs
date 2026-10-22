from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab_3.database import initialize_database
from labs.lab_3.routers import categories, records
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Створити таблиці при старті; дані не заповнювати."""
    initialize_database()
    yield


app = FastAPI(
    title="Облік використання сховищ",
    description=(
        "Сервіс обліку вимірювань заповнення сховищ (logs, backups, archive). "
        "Значення value вимірюється у відсотках зайнятого простору, від 0 до 100."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", summary="Перевірка доступності API", status_code=200)
def ping() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/student", summary="Інформація про студента", status_code=200)
def student() -> dict[str, str | int]:
    return {
        "student_name": STUDENT_NAME,
        "variant_number": VARIANT_NUMBER,
        "group_name": GROUP_NAME,
    }
