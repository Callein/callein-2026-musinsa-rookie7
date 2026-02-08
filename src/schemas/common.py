from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    meta: PaginationMeta


class SingleResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
