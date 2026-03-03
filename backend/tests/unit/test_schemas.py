import pytest
from app.core.schemas import PaginationParams, PaginatedResponse
from pydantic import BaseModel


class TestPaginationParams:
    def test_default_values(self):
        params = PaginationParams()
        assert params.offset == 0
        assert params.limit == 20

    def test_first_page(self):
        params = PaginationParams(page=1, per_page=10)
        assert params.offset == 0
        assert params.limit == 10

    def test_second_page(self):
        params = PaginationParams(page=2, per_page=10)
        assert params.offset == 10
        assert params.limit == 10

    def test_custom_per_page(self):
        params = PaginationParams(page=3, per_page=50)
        assert params.offset == 100
        assert params.limit == 50


class TestPaginatedResponse:
    def test_paginated_response_with_strings(self):
        response = PaginatedResponse[str](
            items=["a", "b", "c"],
            total=100,
            page=1,
            per_page=3,
            pages=34
        )
        assert len(response.items) == 3
        assert response.total == 100
        assert response.pages == 34

    def test_paginated_response_with_model(self):
        class Item(BaseModel):
            id: int
            name: str

        response = PaginatedResponse[Item](
            items=[Item(id=1, name="test")],
            total=1,
            page=1,
            per_page=20,
            pages=1
        )
        assert response.items[0].id == 1
