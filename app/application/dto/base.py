from pydantic import BaseModel, Field
from typing import Optional, TypeVar, Generic, List
from datetime import datetime
from app.shared.enums import SortOrder


T = TypeVar("T")


class BaseResponseDTO(BaseModel):
    success: bool


class DateRange(BaseModel):
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class PaginatedResponseDto(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponseDto[T]":
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class PaginatedReqDto(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
    )
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[SortOrder] = Field(
        default=SortOrder.desc,
        description="Sort direction",
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
