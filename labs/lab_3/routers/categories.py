import sqlite3

from fastapi import APIRouter, HTTPException, Path, status

from labs.lab_3 import repository
from labs.lab_3.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити категорію",
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
)
def create_category(payload: CategoryCreate) -> dict:
    try:
        return repository.create_category(payload.name)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Категорія з назвою '{payload.name}' вже існує",
        ) from None


@router.get(
    "",
    response_model=list[CategoryRead],
    status_code=status.HTTP_200_OK,
    summary="Отримати список категорій",
)
def read_categories() -> list[dict]:
    return repository.list_categories()


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити категорію",
    responses={
        404: {"description": "Категорія не знайдена"},
        409: {"description": "Категорія містить записи і не може бути видалена"},
    },
)
def delete_category(category_id: int = Path(gt=0)) -> None:
    try:
        deleted = repository.delete_category(category_id)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Категорія містить записи",
        ) from None
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категорію не знайдено",
        )
