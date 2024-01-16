import typing as t

import pytest
from ellar.app import App
from ellar.common import NotFound
from ellar.threading import execute_coroutine_with_sync_worker

from ellar_sqlalchemy import (
    EllarSQLAlchemyService,
    first_or_404,
    first_or_404_async,
    get_or_404,
    get_or_404_async,
    model,
    one_or_404,
    one_or_404_async,
)


def _create_model():
    class User(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)

    return User


def _seed_model(app: App):
    user_model = _create_model()
    db_service = app.injector.get(EllarSQLAlchemyService)

    session = db_service.session_factory()

    if session.get_bind().dialect.is_async:
        execute_coroutine_with_sync_worker(db_service.create_all_async())
    else:
        db_service.create_all()

    session.add(user_model(name="First User"))
    res = session.commit()

    if isinstance(res, t.Coroutine):
        execute_coroutine_with_sync_worker(res)

    return user_model


async def test_get_or_404_works(ignore_base, app_ctx, anyio_backend):
    user_model = _seed_model(app_ctx)

    user_instance = get_or_404(user_model, 1)
    assert user_instance.name == "First User"

    with pytest.raises(NotFound):
        get_or_404(user_model, 2)


async def test_get_or_404_async_works(ignore_base, app_ctx_async, anyio_backend):
    if anyio_backend == "asyncio":
        user_model = _seed_model(app_ctx_async)

        user_instance = await get_or_404_async(user_model, 1)
        assert user_instance.name == "First User"

        with pytest.raises(NotFound):
            await get_or_404_async(user_model, 2)


async def test_first_or_404_works(ignore_base, app_ctx, anyio_backend):
    user_model = _seed_model(app_ctx)

    user_instance = first_or_404(model.select(user_model).where(user_model.id == 1))
    assert user_instance.name == "First User"

    with pytest.raises(NotFound):
        first_or_404(model.select(user_model).where(user_model.id == 2))


async def test_first_or_404_async_works(ignore_base, app_ctx_async, anyio_backend):
    if anyio_backend == "asyncio":
        user_model = _seed_model(app_ctx_async)

        user_instance = await first_or_404_async(
            model.select(user_model).where(user_model.id == 1)
        )
        assert user_instance.name == "First User"

        with pytest.raises(NotFound):
            await first_or_404_async(model.select(user_model).where(user_model.id == 2))


async def test_one_or_404_works(ignore_base, app_ctx, anyio_backend):
    user_model = _seed_model(app_ctx)

    user_instance = one_or_404(model.select(user_model).where(user_model.id == 1))
    assert user_instance.name == "First User"

    with pytest.raises(NotFound):
        one_or_404(model.select(user_model).where(user_model.id == 2))


async def test_one_or_404_async_works(ignore_base, app_ctx_async, anyio_backend):
    if anyio_backend == "asyncio":
        user_model = _seed_model(app_ctx_async)

        user_instance = await one_or_404_async(
            model.select(user_model).where(user_model.id == 1)
        )
        assert user_instance.name == "First User"

        with pytest.raises(NotFound):
            await one_or_404_async(model.select(user_model).where(user_model.id == 2))
