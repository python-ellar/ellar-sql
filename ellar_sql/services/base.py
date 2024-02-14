import os
import typing as t
from threading import get_ident
from weakref import WeakKeyDictionary

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
import sqlalchemy.orm as sa_orm
from ellar.common.exceptions import ImproperConfiguration
from ellar.threading.sync_worker import execute_coroutine
from ellar.utils.importer import (
    get_main_directory_by_stack,
    module_import,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
)

from ellar_sql.constant import (
    DEFAULT_KEY,
)
from ellar_sql.model import (
    make_metadata,
)
from ellar_sql.model.database_binds import get_all_metadata, get_metadata
from ellar_sql.schemas import MigrationOption
from ellar_sql.session import ModelSession

from .metadata_engine import MetaDataEngine


class EllarSQLService:
    def __init__(
        self,
        databases: t.Union[str, t.Dict[str, t.Any]],
        *,
        common_session_options: t.Optional[t.Dict[str, t.Any]] = None,
        common_engine_options: t.Optional[t.Dict[str, t.Any]] = None,
        models: t.Optional[t.List[str]] = None,
        echo: bool = False,
        root_path: t.Optional[str] = None,
        migration_options: t.Optional[MigrationOption] = None,
    ) -> None:
        self._engines: WeakKeyDictionary[
            "EllarSQLService",
            t.Dict[str, sa.engine.Engine],
        ] = WeakKeyDictionary()

        self._engines.setdefault(self, {})
        self._session_options = common_session_options or {}

        self._common_engine_options = common_engine_options or {}
        self._execution_path = get_main_directory_by_stack(root_path or "__main__", 2)

        self.migration_options = migration_options or MigrationOption(
            directory="migrations"
        )
        self.migration_options.validate_directory(self._execution_path)
        self._has_async_engine_driver: bool = False

        self._setup(databases, models=models, echo=echo)
        self.session_factory = self.get_scoped_session()

    @property
    def has_async_engine_driver(self) -> bool:
        return self._has_async_engine_driver

    @property
    def engines(self) -> t.Dict[str, sa.Engine]:
        return dict(self._engines[self])

    @property
    def engine(self) -> sa.Engine:
        assert self._engines[self].get(
            DEFAULT_KEY
        ), f"{self.__class__.__name__} configuration is not ready"
        return self._engines[self][DEFAULT_KEY]

    def _setup(
        self,
        databases: t.Union[str, t.Dict[str, t.Any]],
        models: t.Optional[t.List[str]] = None,
        echo: bool = False,
    ) -> None:
        for model in models or []:
            module_import(model)

        self._build_engines(databases, echo)

    def _build_engines(
        self, databases: t.Union[str, t.Dict[str, t.Any]], echo: bool
    ) -> None:
        engine_options: t.Dict[str, t.Dict[str, t.Any]] = {}

        if isinstance(databases, str):
            common_engine_options = self._common_engine_options.copy()
            common_engine_options["url"] = databases
            engine_options.setdefault(DEFAULT_KEY, {}).update(common_engine_options)

        elif isinstance(databases, dict):
            for key, value in databases.items():
                engine_options[key] = self._common_engine_options.copy()

                if isinstance(value, (str, sa.engine.URL)):
                    engine_options[key]["url"] = value
                else:
                    engine_options[key].update(value)
        else:
            raise ImproperConfiguration(
                "Invalid databases data structure. Allowed datastructure, str or dict data type"
            )

        if DEFAULT_KEY not in engine_options:
            raise ImproperConfiguration(
                f"`default` database must be present in databases parameter: {databases}"
            )

        engines = self._engines.setdefault(self, {})

        for key, options in engine_options.items():
            make_metadata(key)

            options.setdefault("echo", echo)
            options.setdefault("echo_pool", echo)

            self._validate_engine_option_defaults(options)
            engines[key] = self._make_engine(options)

        found_async_engine = [
            engine for engine in engines.values() if engine.dialect.is_async
        ]
        if found_async_engine and len(found_async_engine) != len(engines):
            raise Exception(
                "Databases Configuration must either be all async or all synchronous type"
            )

        self._has_async_engine_driver = bool(len(found_async_engine))

    def __validate_databases_input(self, *databases: str) -> t.Union[str, t.List[str]]:
        _databases: t.Union[str, t.List[str]] = list(databases)
        if len(_databases) == 0:
            _databases = "__all__"
        return _databases

    def create_all(self, *databases: str) -> None:
        _databases = self.__validate_databases_input(*databases)

        metadata_engines = self._get_metadata_and_engine(_databases)

        for metadata_engine in metadata_engines:
            if metadata_engine.is_async():
                execute_coroutine(metadata_engine.create_all_async())
                continue
            metadata_engine.create_all()

    def drop_all(self, *databases: str) -> None:
        _databases = self.__validate_databases_input(*databases)

        metadata_engines = self._get_metadata_and_engine(_databases)

        for metadata_engine in metadata_engines:
            if metadata_engine.is_async():
                execute_coroutine(metadata_engine.drop_all_async())
                continue
            metadata_engine.drop_all()

    def reflect(self, *databases: str) -> None:
        _databases = self.__validate_databases_input(*databases)

        metadata_engines = self._get_metadata_and_engine(_databases)

        for metadata_engine in metadata_engines:
            if metadata_engine.is_async():
                execute_coroutine(metadata_engine.reflect_async())
                continue
            metadata_engine.reflect()

    def get_scoped_session(
        self,
        **extra_options: t.Any,
    ) -> t.Union[
        sa_orm.scoped_session[sa_orm.Session],
        async_scoped_session[t.Union[AsyncSession, t.Any]],
    ]:
        options = self._session_options.copy()
        options.update(extra_options)

        scope = options.pop("scopefunc", get_ident)

        factory = self._make_session_factory(options)

        if self.has_async_engine_driver:
            return async_scoped_session(factory, scope)  # type:ignore[arg-type]

        return sa_orm.scoped_session(factory, scope)  # type:ignore[arg-type]

    def _make_session_factory(
        self, options: t.Dict[str, t.Any]
    ) -> t.Union[sa_orm.sessionmaker[sa_orm.Session], async_sessionmaker[AsyncSession]]:
        if self.has_async_engine_driver:
            options.setdefault("sync_session_class", ModelSession)
        else:
            options.setdefault("class_", ModelSession)

        session_class = options.get("class_", options.get("sync_session_class"))

        if session_class is ModelSession or issubclass(session_class, ModelSession):
            options.update(engines=self._engines[self])

        if self.has_async_engine_driver:
            return async_sessionmaker(**options)

        return sa_orm.sessionmaker(**options)

    def _validate_engine_option_defaults(self, options: t.Dict[str, t.Any]) -> None:
        url = sa.engine.make_url(options["url"])

        if url.drivername in {"sqlite", "sqlite+pysqlite", "sqlite+aiosqlite"}:
            if url.database is None or url.database in {"", ":memory:"}:
                options["poolclass"] = sa.pool.StaticPool

                if "connect_args" not in options:
                    options["connect_args"] = {}

                options["connect_args"]["check_same_thread"] = False

            elif self._execution_path:
                is_uri = url.query.get("uri", False)

                if is_uri:
                    db_str = url.database[5:]
                else:
                    db_str = url.database

                if not os.path.isabs(db_str):
                    root_path = os.path.join(self._execution_path, "sqlite")
                    os.makedirs(root_path, exist_ok=True)
                    db_str = os.path.join(root_path, db_str)

                    if is_uri:
                        db_str = f"file:{db_str}"

                options["url"] = url.set(database=db_str)

        elif url.drivername.startswith("mysql"):
            # set queue defaults only when using queue pool
            if (
                "pool_class" not in options
                or options["pool_class"] is sa.pool.QueuePool
            ):
                options.setdefault("pool_recycle", 7200)

            if "charset" not in url.query:
                options["url"] = url.update_query_dict({"charset": "utf8mb4"})

    def _make_engine(self, options: t.Dict[str, t.Any]) -> sa.engine.Engine:
        engine = sa.engine_from_config(options, prefix="")

        # if engine.dialect.is_async:
        #     return AsyncEngine(engine)

        return engine

    def _get_metadata_and_engine(
        self, database: t.Union[str, t.List[str]] = "__all__"
    ) -> t.List[MetaDataEngine]:
        engines = self._engines[self]

        if database == "__all__":
            keys: t.List[str] = list(get_all_metadata())
        elif isinstance(database, str):
            keys = [database]
        else:
            keys = database

        result: t.List[MetaDataEngine] = []

        for key in keys:
            try:
                engine = engines[key]
            except KeyError:
                message = f"Bind key '{key}' is not in 'Database' config."
                raise sa_exc.UnboundExecutionError(message) from None

            db_metadata = get_metadata(key, certain=True)
            result.append(MetaDataEngine(metadata=db_metadata.metadata, engine=engine))
        return result
