import typing as t

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from ellar.threading import run_as_async
from factory.alchemy import (
    SESSION_PERSISTENCE_COMMIT,
    SESSION_PERSISTENCE_FLUSH,
    SQLAlchemyModelFactory,
    SQLAlchemyOptions,
)
from factory.errors import FactoryError
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ellar_sql.model.base import ModelBase

T = t.TypeVar("T", bound=ModelBase)


class EllarSQLOptions(SQLAlchemyOptions):
    @staticmethod
    def _check_has_sqlalchemy_session_set(meta, value):
        if value and hasattr(meta, "sqlalchemy_session"):
            raise RuntimeError(
                "Provide either a sqlalchemy_session or a sqlalchemy_session_factory, not both"
            )


class EllarSQLFactory(SQLAlchemyModelFactory):
    """Factory for EllarSQL models."""

    _options_class = EllarSQLOptions

    class Meta:
        abstract = True

    @classmethod
    @run_as_async
    async def _session_execute(
        cls, session_func: t.Callable, *args: t.Any, **kwargs: t.Any
    ) -> t.Union[sa.Result, sa.CursorResult, t.Any]:
        res = session_func(*args, **kwargs)
        if isinstance(res, t.Coroutine):
            res = await res
        return res

    @classmethod
    def _get_or_create(
        cls,
        model_class: t.Type[T],
        session: t.Union[sa_orm.Session, AsyncSession],
        args: t.Tuple[t.Any],
        kwargs: t.Dict[str, t.Any],
    ):
        key_fields = {}
        for field in cls._meta.sqlalchemy_get_or_create:
            if field not in kwargs:
                raise FactoryError(
                    "sqlalchemy_get_or_create - "
                    "Unable to find initialization value for '%s' in factory %s"
                    % (field, cls.__name__)
                )
            key_fields[field] = kwargs.pop(field)
        stmt = sa.select(model_class).filter_by(*args, **key_fields)  # type:ignore[call-arg]

        res = cls._session_execute(session.execute, stmt)
        obj = res.scalar()

        if not obj:
            try:
                obj = cls._save(model_class, session, args, {**key_fields, **kwargs})
            except IntegrityError as e:
                cls._session_execute(session.rollback)

                if cls._original_params is None:
                    raise e

                get_or_create_params = {
                    lookup: value
                    for lookup, value in cls._original_params.items()
                    if lookup in cls._meta.sqlalchemy_get_or_create
                }
                if get_or_create_params:
                    try:
                        stmt = sa.select(model_class).filter_by(**get_or_create_params)
                        res = cls._session_execute(session.execute, stmt)
                        obj = res.scalar_one()
                    except NoResultFound:
                        # Original params are not a valid lookup and triggered a create(),
                        # that resulted in an IntegrityError.
                        raise e from None
                else:
                    raise e

        return obj

    @classmethod
    def _save(
        cls,
        model_class: t.Type[T],
        session: t.Union[sa_orm.Session, AsyncSession],
        args: t.Tuple[t.Any],
        kwargs: t.Dict[str, t.Any],
    ) -> T:
        session_persistence = cls._meta.sqlalchemy_session_persistence

        obj = model_class(*args, **kwargs)  # type:ignore[call-arg]
        session.add(obj)
        if session_persistence == SESSION_PERSISTENCE_FLUSH:
            cls._session_execute(session.flush)
        elif session_persistence == SESSION_PERSISTENCE_COMMIT:
            cls._session_execute(session.commit)
            cls._session_execute(session.refresh, obj)
        return obj
