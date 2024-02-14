import typing as t

import ellar.common as ecm
import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
from ellar.app import current_injector

from ellar_sql.services import EllarSQLService

_O = t.TypeVar("_O", bound=object)


async def get_or_404(
    entity: t.Type[_O],
    ident: t.Any,
    *,
    error_message: t.Optional[str] = None,
    **kwargs: t.Any,
) -> _O:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.get_scoped_session()()

    value = session.get(entity, ident, **kwargs)

    if isinstance(value, t.Coroutine):
        value = await value

    if value is None:
        raise ecm.NotFound(detail=error_message)

    return t.cast(_O, value)


async def get_or_none(
    entity: t.Type[_O],
    ident: t.Any,
    **kwargs: t.Any,
) -> t.Optional[_O]:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.get_scoped_session()()

    value = session.get(entity, ident, **kwargs)

    if isinstance(value, t.Coroutine):
        value = await value

    if value is None:
        return None

    return t.cast(_O, value)


async def first_or_404(
    statement: sa.sql.Select[t.Any], *, error_message: t.Optional[str] = None
) -> t.Any:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    result = session.execute(statement)
    if isinstance(result, t.Coroutine):
        result = await result

    value = result.scalar()

    if value is None:
        raise ecm.NotFound(detail=error_message)

    return value


async def first_or_none(statement: sa.sql.Select[t.Any]) -> t.Any:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    result = session.execute(statement)
    if isinstance(result, t.Coroutine):
        result = await result

    value = result.scalar()

    if value is None:
        return None

    return value


async def one_or_404(
    statement: sa.sql.Select[t.Any], *, error_message: t.Optional[str] = None
) -> t.Any:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    try:
        result = session.execute(statement)

        if isinstance(result, t.Coroutine):
            result = await result

        return result.scalar_one()
    except (sa_exc.NoResultFound, sa_exc.MultipleResultsFound) as ex:
        raise ecm.NotFound(detail=error_message) from ex
