from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class PaginationParams:
    def __init__(self, page: int = 1, per_page: int = 20):
        self.offset = (page - 1) * per_page
        self.limit = per_page

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int