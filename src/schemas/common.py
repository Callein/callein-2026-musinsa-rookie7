from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """페이지네이션 메타데이터 스키마"""
    total: int
    page: int
    limit: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션된 응답 스키마"""
    success: bool = True
    data: list[T]
    meta: PaginationMeta


class SingleResponse(BaseModel, Generic[T]):
    """단일 객체 응답 스키마"""
    success: bool = True
    data: T


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    success: bool = False
    error: str
