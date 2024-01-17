import typing as t

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
import sqlalchemy.orm as sa_orm

from ellar_sql.constant import DEFAULT_KEY

EngineType = t.Optional[t.Union[sa.engine.Engine, sa.engine.Connection]]


def _get_engine_from_clause(
    clause: t.Optional[sa.ClauseElement],
    engines: t.Mapping[str, sa.Engine],
) -> t.Optional[sa.Engine]:
    table = None

    if clause is not None:
        if isinstance(clause, sa.Table):
            table = clause
        elif isinstance(clause, sa.UpdateBase) and isinstance(clause.table, sa.Table):
            table = clause.table

    if table is not None and "database_bind_key" in table.metadata.info:
        key = table.metadata.info["database_bind_key"]

        if key not in engines:
            raise sa_exc.UnboundExecutionError(
                f"Database Bind key '{key}' is not in 'Database' config."
            )

        return engines[key]

    return None


class ModelSession(sa_orm.Session):
    def __init__(self, engines: t.Mapping[str, sa.Engine], **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self._engines = engines
        self._model_changes: t.Dict[object, t.Tuple[t.Any, str]] = {}

    def get_bind(  # type:ignore[override]
        self,
        mapper: t.Optional[t.Any] = None,
        clause: t.Optional[t.Any] = None,
        bind: EngineType = None,
        **kwargs: t.Any,
    ) -> EngineType:
        if bind is not None:
            return bind

        engines = self._engines

        if mapper is not None:
            try:
                mapper = sa.inspect(mapper)
            except sa_exc.NoInspectionAvailable as e:
                if isinstance(mapper, type):
                    raise sa_orm.exc.UnmappedClassError(mapper) from e

                raise

            engine = _get_engine_from_clause(mapper.local_table, engines)

            if engine is not None:
                return engine

        if clause is not None:
            engine = _get_engine_from_clause(clause, engines)

            if engine is not None:
                return engine

        if DEFAULT_KEY in engines:
            return engines[DEFAULT_KEY]

        return super().get_bind(mapper=mapper, clause=clause, bind=bind, **kwargs)
