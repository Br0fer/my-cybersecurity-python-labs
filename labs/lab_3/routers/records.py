import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from labs.lab_3 import repository
from labs.lab_3.config import MAX_VALUE, MIN_VALUE
from labs.lab_3.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["records"])


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запис",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Запис із таким code вже існує"},
    },
)
def create_record(payload: RecordCreate) -> dict:
    """Створити вимірювання заповнення сховища."""
    try:
        return repository.create_record(**payload.model_dump())
    except sqlite3.IntegrityError as error:
        if "FOREIGN KEY" in str(error):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категорію не знайдено",
            ) from None
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Запис із code '{payload.code}' вже існує",
        ) from None


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    status_code=status.HTTP_200_OK,
    summary="Отримати запис за ID",
    responses={404: {"description": "Запис не знайдено"}},
)
def get_record(record_id: int = Path(gt=0)) -> dict:
    record = repository.get_record(record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено",
        )
    return record


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    responses={404: {"description": "Запис не знайдено"}},
)
def delete_request(record_id: int = Path(gt=0)) -> None:
    deleted = repository.delete_record(record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено",
        )


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    status_code=status.HTTP_200_OK,
    summary="Повністю замінити запис",
    responses={
        404: {"description": "Запис або категорію не знайдено"},
        409: {"description": "Запис із таким code вже існує"},
    },
)
def replace_record(
    payload: RecordReplace,
    record_id: int = Path(gt=0),
) -> dict:
    """Замінити всі змінювані поля запису; id лишається незмінним."""
    try:
        record = repository.replace_record(record_id, **payload.model_dump())
    except sqlite3.IntegrityError as error:
        if "FOREIGN KEY" in str(error):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категорію не знайдено",
            ) from None
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Запис із code '{payload.code}' вже існує",
        ) from None
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено",
        )
    return record


@router.get(
    "",
    response_model=list[RecordRead],
    status_code=status.HTTP_200_OK,
    summary="Список записів із фільтрами та пагінацією",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    status_filter: Annotated[
        Literal["new", "in_progress", "done"] | None,
        Query(alias="status", description="Лише записи з цим статусом"),
    ] = None,
    min_value: Annotated[
        float | None,
        Query(
            ge=MIN_VALUE,
            le=MAX_VALUE,
            allow_inf_nan=False,
            description="Мінімум value, %",
        ),
    ] = None,
    q: Annotated[
        str | None,
        Query(min_length=1, max_length=120, description="Підрядок у title"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Макс. кількість")] = 20,
    offset: Annotated[int, Query(ge=0, description="Скільки записів пропустити")] = 0,
) -> list[dict]:
    """Повернути записи за фільтрами, відсортовані за id."""
    return repository.list_records(
        category_id=category_id,
        status=status_filter,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетне створення записів в одній транзакції",
    responses={
        404: {"description": "Одну з категорій не знайдено, нічого не збережено"},
        409: {"description": "Дубль code, нічого не збережено"},
    },
)
def create_records_bulk(
    records: Annotated[list[RecordCreate], Body(min_length=1, max_length=100)],
) -> list[dict]:
    """Додати від 1 до 100 записів атомарно: усі або жодного."""
    try:
        return repository.create_records_bulk([r.model_dump() for r in records])
    except repository.CategoryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категорію {error.category_id} не знайдено",
        ) from None
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Дубль code у пакеті або в базі; нічого не збережено",
        ) from None
