import typing as t

import ellar.common as ecm
import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
from ellar.app import current_injector

from ellar_sql.services import EllarSQLService

_O = t.TypeVar("_O", bound=object)


def get_or_404(
    entity: t.Type[_O],
    ident: t.Any,
    *,
    error_message: t.Optional[str] = None,
    **kwargs: t.Any,
) -> _O:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    value = session.get(entity, ident, **kwargs)

    if value is None:
        raise ecm.NotFound(detail=error_message)

    return t.cast(_O, value)


async def get_or_404_async(
    entity: t.Type[_O],
    ident: t.Any,
    *,
    error_message: t.Optional[str] = None,
    **kwargs: t.Any,
) -> _O:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    value = await session.get(entity, ident, **kwargs)

    if value is None:
        raise ecm.NotFound(detail=error_message)

    return t.cast(_O, value)


def first_or_404(
    statement: sa.sql.Select[t.Any], *, error_message: t.Optional[str] = None
) -> t.Any:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    value = session.execute(statement).scalar()

    if value is None:
        raise ecm.NotFound(detail=error_message)

    return value


async def first_or_404_async(
    statement: sa.sql.Select[t.Any], *, error_message: t.Optional[str] = None
) -> t.Any:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    res = await session.execute(statement)
    value = res.scalar()

    if value is None:
        raise ecm.NotFound(detail=error_message)

    return value


def one_or_404(
    statement: sa.sql.Select[t.Any], *, error_message: t.Optional[str] = None
) -> t.Any:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    try:
        return session.execute(statement).scalar_one()
    except (sa_exc.NoResultFound, sa_exc.MultipleResultsFound) as ex:
        raise ecm.NotFound(detail=error_message) from ex


async def one_or_404_async(
    statement: sa.sql.Select[t.Any], *, error_message: t.Optional[str] = None
) -> t.Any:
    """ """
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    try:
        res = await session.execute(statement)
        return res.scalar_one()
    except (sa_exc.NoResultFound, sa_exc.MultipleResultsFound) as ex:
        raise ecm.NotFound(detail=error_message) from ex
