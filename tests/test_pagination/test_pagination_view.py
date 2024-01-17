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
    kwargs = dict(kw, template_context=True, pagination_class=pagination_class)
    if case_2:
        kwargs.update(model=user_model)

    @ecm.get("/list")
    @ecm.render("list")
    @paginate(**kwargs)
    def html_pagination():
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
def test_paginate_template_case_1(ignore_base, app_setup, pagination_class, kw):
    app = app_setup(base_directory=base, template_folder="templates")
    user_model = seed_100_users(app)

    app.router.append(_get_route_test_route(user_model, pagination_class, **kw))
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
def test_paginate_template_case_2(ignore_base, app_setup, pagination_class, kw):
    app = app_setup(base_directory=base, template_folder="templates")
    user_model = seed_100_users(app)

    app.router.append(
        _get_route_test_route(user_model, pagination_class, case_2=True, **kw)
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
def test_paginate_template_case_3(ignore_base, app_setup, pagination_class, kw):
    app = app_setup(base_directory=base, template_folder="templates")
    user_model = seed_100_users(app)

    app.router.append(
        _get_route_test_route(user_model, pagination_class, case_3=True, **kw)
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
def test_paginate_template_case_invalid(ignore_base, app_setup, pagination_class, kw):
    app = app_setup(base_directory=base, template_folder="templates")
    user_model = seed_100_users(app)

    app.router.append(
        _get_route_test_route(user_model, pagination_class, invalid=True, **kw)
    )
    client = TestClient(app, raise_server_exceptions=False)

    res = client.get("/list")
    assert res.status_code == 500


def test_api_paginate_case_1(ignore_base, app_setup):
    app = app_setup()
    user_model = seed_100_users(app)

    @ecm.get("/list")
    @paginate(item_schema=UserSerializer, per_page=5)
    def paginated_user():
        return model.select(user_model)

    app.router.append(paginated_user)
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


def test_api_paginate_case_2(ignore_base, app_setup):
    app = app_setup()
    user_model = seed_100_users(app)

    @ecm.get("/list")
    @paginate(item_schema=UserSerializer, per_page=10)
    def paginated_user():
        return user_model

    app.router.append(paginated_user)
    client = TestClient(app)

    res = client.get("/list?page=10")

    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 10
    assert data["next"] is None

    res = client.get("/list?page=2")
    data = res.json()
    assert data["next"] == "http://testserver/list?page=3"
    assert data["previous"] == "http://testserver/list"


def test_api_paginate_case_3(ignore_base, app_setup):
    app = app_setup()
    user_model = seed_100_users(app)

    @ecm.get("/list")
    @paginate(model=user_model, item_schema=UserSerializer, per_page=5)
    def paginated_user():
        pass

    app.router.append(paginated_user)
    client = TestClient(app)

    res = client.get("/list")

    assert res.status_code == 200
    assert len(res.json()["items"]) == 5


def test_api_paginate_case_invalid(ignore_base, app_setup):
    with pytest.raises(ecm.exceptions.ImproperConfiguration):

        @ecm.get("/list")
        @paginate(per_page=5)
        def paginated_user():
            pass


def test_api_paginate_with_limit_offset_case_1(ignore_base, app_setup):
    app = app_setup()
    user_model = seed_100_users(app)

    @ecm.get("/list")
    @paginate(
        item_schema=UserSerializer,
        pagination_class=LimitOffsetPagination,
        limit=5,
        max_limit=10,
    )
    def paginated_user():
        return user_model

    app.router.append(paginated_user)
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


def test_api_paginate_with_limit_offset_case_2(ignore_base, app_setup):
    app = app_setup()
    user_model = seed_100_users(app)

    @ecm.get("/list")
    @paginate(
        item_schema=UserSerializer,
        pagination_class=LimitOffsetPagination,
        limit=5,
        max_limit=10,
    )
    def paginated_user():
        return model.select(user_model)

    app.router.append(paginated_user)
    client = TestClient(app)

    res = client.get("/list?limit=5&offset=2")

    assert res.status_code == 200
    assert len(res.json()["items"]) == 5
    assert res.json()["items"][0] == {"id": 6, "name": "User Number 6"}


def test_api_paginate_with_limit_offset_case_3(ignore_base, app_setup):
    app = app_setup()
    user_model = seed_100_users(app)

    @ecm.get("/list")
    @paginate(
        model=user_model,
        item_schema=UserSerializer,
        pagination_class=LimitOffsetPagination,
        limit=5,
        max_limit=10,
    )
    def paginated_user():
        pass

    app.router.append(paginated_user)
    client = TestClient(app)

    res = client.get("/list?limit=5&offset=2")

    assert res.status_code == 200
    assert len(res.json()["items"]) == 5
    assert res.json()["items"][0] == {"id": 6, "name": "User Number 6"}


def test_api_paginate_with_limit_offset_case_invalid(ignore_base, app_setup):
    with pytest.raises(ecm.exceptions.ImproperConfiguration):

        @ecm.get("/list")
        @paginate(pagination_class=LimitOffsetPagination)
        def paginated_user():
            pass
