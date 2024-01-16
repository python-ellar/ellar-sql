import pytest
from ellar.common import NotFound

from ellar_sqlalchemy import EllarSQLAlchemyService
from ellar_sqlalchemy.pagination import Paginator

from .seed import create_model, seed_100_users


async def test_user_model_paginator(ignore_base, app_ctx, anyio_backend):
    user_model = seed_100_users(app_ctx)
    page1 = Paginator(model=user_model, per_page=25, page=1, count=True)
    assert page1.page == 1

    assert page1.per_page == 25
    assert len(page1.items) == 25

    assert page1.total == 100
    assert page1.pages == 4


async def test_user_model_paginator_async(ignore_base, app_ctx_async, anyio_backend):
    user_model = seed_100_users(app_ctx_async)
    page2 = Paginator(model=user_model, per_page=25, page=2, count=True)
    assert page2.page == 2

    assert page2.per_page == 25
    assert len(page2.items) == 25

    assert page2.total == 100
    assert page2.pages == 4
    page1 = page2.prev(error_out=True)
    assert page1.total == 100
    assert page1.has_prev is False


async def test_paginate_qs(ignore_base, app_ctx, anyio_backend):
    user_model = seed_100_users(app_ctx)

    p = Paginator(model=user_model, page=2, per_page=10)
    assert p.page == 2
    assert p.per_page == 10


async def test_paginate_max(ignore_base, app_ctx, anyio_backend):
    user_model = seed_100_users(app_ctx)

    p = Paginator(model=user_model, per_page=100, max_per_page=50)
    assert p.per_page == 50


async def test_next_page_size(ignore_base, app_ctx, anyio_backend):
    user_model = seed_100_users(app_ctx)

    p = Paginator(model=user_model, per_page=25, max_per_page=50)
    assert p.page == 1
    assert p.per_page == 25

    p = p.next()
    assert p.page == 2
    assert p.per_page == 25


async def test_no_count(ignore_base, app_ctx, anyio_backend):
    user_model = seed_100_users(app_ctx)

    p = Paginator(model=user_model, count=False)
    assert p.total is None


async def test_no_items_404(ignore_base, app_ctx, anyio_backend):
    user_model = create_model()
    db_service = app_ctx.injector.get(EllarSQLAlchemyService)

    db_service.create_all()

    p = Paginator(model=user_model)
    assert len(p.items) == 0

    with pytest.raises(NotFound):
        p.next(error_out=True)

    with pytest.raises(NotFound):
        p.prev(error_out=True)


async def test_error_out(ignore_base, app_ctx, anyio_backend):
    user_model = create_model()
    db_service = app_ctx.injector.get(EllarSQLAlchemyService)

    db_service.create_all()
    for page, per_page in [(-2, 5), (1, -5)]:
        with pytest.raises(NotFound):
            Paginator(model=user_model, page=page, per_page=per_page)

    for page, per_page in [(-2, -5), (-1, 0)]:
        p = Paginator(model=user_model, page=page, per_page=per_page, error_out=False)
        assert p.per_page == 20
        assert p.page == 1
