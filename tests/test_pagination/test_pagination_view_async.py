from pathlib import Path

import ellar.common as ecm
import pytest
from ellar.testing import TestClient

from ellar_sql import (
    LimitOffsetPagination,
    PageNumberPagination,
    model,
    paginate,
)

from .seed import seed_100_users

base = Path(__file__).parent


class UserSerializer(ecm.Serializer):
    id: int
    name: str


def _get_route_test_route(
    user_model, pagination_class, case_2=False, case_3=False, invalid=False, **kw
):
    kwargs = dict(kw, as_template_context=True, pagination_class=pagination_class)
    if case_2:
        kwargs.update(model=user_model)

    @ecm.get("/list")
    @ecm.render("list")
    @paginate(**kwargs)
    async def html_pagination():
        if case_2:
            return {"name": "Ellar Pagination"}

        if case_3:
            return model.select(user_model)

        if invalid:
            return []

        return model.select(user_model), {"name": "Ellar Pagination"}

    return html_pagination


@pytest.mark.parametrize(
    "pagination_class, kw",
    [(LimitOffsetPagination, {"limit": 5}), (PageNumberPagination, {"per_page": 5})],
)
def test_paginate_template_case_1_async(ignore_base, app_setup, pagination_class, kw):
    user_model = seed_100_users()
    app = app_setup(
        base_directory=base,
        template_folder="templates",
        routers=[_get_route_test_route(user_model, pagination_class, **kw)],
    )
    client = TestClient(app)

    res = client.get("/list")
    assert res.status_code == 200

    assert '<a href="http://testserver/list?page=2">2</a>' in res.text
    assert '<a href="http://testserver/list?page=20">20</a>' in res.text
    assert "<li>1 @ User Number 1" in res.text
    assert "<li>5 @ User Number 5" in res.text
    assert "Ellar Pagination" in res.text


@pytest.mark.parametrize(
    "pagination_class, kw",
    [(LimitOffsetPagination, {"limit": 5}), (PageNumberPagination, {"per_page": 5})],
)
def test_paginate_template_case_2_async(ignore_base, app_setup, pagination_class, kw):
    user_model = seed_100_users()
    app = app_setup(
        base_directory=base,
        template_folder="templates",
        routers=[
            _get_route_test_route(user_model, pagination_class, case_2=True, **kw)
        ],
    )

    client = TestClient(app)

    res = client.get("/list")
    assert res.status_code == 200

    assert '<a href="http://testserver/list?page=2">2</a>' in res.text
    assert '<a href="http://testserver/list?page=20">20</a>' in res.text
    assert "<li>1 @ User Number 1" in res.text
    assert "<li>5 @ User Number 5" in res.text
    assert "Ellar Pagination" in res.text


@pytest.mark.parametrize(
    "pagination_class, kw",
    [(LimitOffsetPagination, {"limit": 5}), (PageNumberPagination, {"per_page": 5})],
)
def test_paginate_template_case_3_async(ignore_base, app_setup, pagination_class, kw):
    user_model = seed_100_users()
    app = app_setup(
        base_directory=base,
        template_folder="templates",
        routers=[
            _get_route_test_route(user_model, pagination_class, case_3=True, **kw)
        ],
    )

    client = TestClient(app)

    res = client.get("/list")
    assert res.status_code == 200

    assert '<a href="http://testserver/list?page=2">2</a>' in res.text
    assert '<a href="http://testserver/list?page=20">20</a>' in res.text
    assert "<li>1 @ User Number 1" in res.text
    assert "<li>5 @ User Number 5" in res.text
    assert "Ellar Pagination" not in res.text


@pytest.mark.parametrize(
    "pagination_class, kw",
    [(LimitOffsetPagination, {"limit": 5}), (PageNumberPagination, {"per_page": 5})],
)
def test_paginate_template_case_invalid_async(
    ignore_base, app_setup, pagination_class, kw
):
    user_model = seed_100_users()
    app = app_setup(
        base_directory=base,
        template_folder="templates",
        routers=[
            _get_route_test_route(user_model, pagination_class, invalid=True, **kw)
        ],
    )

    client = TestClient(app, raise_server_exceptions=False)

    res = client.get("/list")
    assert res.status_code == 500


def test_api_paginate_case_1_async(ignore_base, app_setup):
    user_model = seed_100_users()

    @ecm.get("/list")
    @paginate(item_schema=UserSerializer, per_page=5)
    async def paginated_user():
        return model.select(user_model)

    app = app_setup(routers=[paginated_user])
    client = TestClient(app)

    res = client.get("/list")

    assert res.status_code == 200
    assert res.json() == {
        "count": 100,
        "next": "http://testserver/list?page=2",
        "previous": None,
        "items": [
            {"id": 1, "name": "User Number 1"},
            {"id": 2, "name": "User Number 2"},
            {"id": 3, "name": "User Number 3"},
            {"id": 4, "name": "User Number 4"},
            {"id": 5, "name": "User Number 5"},
        ],
    }


def test_api_paginate_with_limit_offset_case_1_async(ignore_base, app_setup):
    user_model = seed_100_users()

    @ecm.get("/list")
    @paginate(
        item_schema=UserSerializer,
        pagination_class=LimitOffsetPagination,
        limit=5,
        max_limit=10,
    )
    async def paginated_user():
        return user_model

    app = app_setup(routers=[paginated_user])
    client = TestClient(app)

    res = client.get("/list")

    assert res.status_code == 200
    assert res.json() == {
        "count": 100,
        "items": [
            {"id": 1, "name": "User Number 1"},
            {"id": 2, "name": "User Number 2"},
            {"id": 3, "name": "User Number 3"},
            {"id": 4, "name": "User Number 4"},
            {"id": 5, "name": "User Number 5"},
        ],
    }

    res = client.get("/list?limit=10")

    assert res.status_code == 200
    assert len(res.json()["items"]) == 10

    res = client.get("/list?limit=20")

    assert res.status_code == 200
    assert len(res.json()["items"]) == 10
