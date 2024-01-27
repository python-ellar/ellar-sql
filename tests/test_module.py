import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ellar_sql import model


async def test_invalid_session_engine_ioc_resolve_for_sync_setup(
    app_setup, anyio_backend
):
    app = app_setup()

    with pytest.raises(RuntimeError) as ex:
        app.injector.get(AsyncEngine)

    assert "<class 'sqlalchemy.engine.base.Engine'>" in str(ex.value)

    with pytest.raises(RuntimeError) as ex1:
        app.injector.get(AsyncSession)

    assert "<class 'sqlalchemy.orm.session.Session'>" in str(ex1.value)


async def test_invalid_session_engine_ioc_resolve_for_async_setup(
    app_setup_async, anyio_backend
):
    app = app_setup_async()

    with pytest.raises(RuntimeError) as ex:
        app.injector.get(model.Session)
    assert "<class 'sqlalchemy.ext.asyncio.session.AsyncSession'>" in str(ex.value)

    with pytest.raises(RuntimeError) as ex1:
        app.injector.get(model.Engine)

    assert "<class 'sqlalchemy.ext.asyncio.engine.AsyncEngine'>" in str(ex1.value)
