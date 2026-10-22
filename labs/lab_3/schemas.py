from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab_3.config import MAX_VALUE, MIN_VALUE


class RecordCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
    code: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=120)
    category_id: int = Field(gt=0)
    value: float = Field(ge=MIN_VALUE, le=MAX_VALUE, allow_inf_nan=False)
    status: Literal["new", "in_progress", "done"]


class RecordRead(RecordCreate):
    id: int
    category_name: str


class RecordUpdate(RecordCreate):
    pass


class CategoryCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str = Field(min_length=2, max_length=40)


class CategoryRead(BaseModel):
    id: int
    name: str
