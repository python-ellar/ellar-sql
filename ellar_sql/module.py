import functools
import typing as t

import sqlalchemy as sa
from ellar.common import IHostContext, IModuleSetup, Module
from ellar.core import Config, DynamicModule, ModuleBase, ModuleSetup
from ellar.core.middleware import as_middleware
from ellar.core.modules import ModuleRefBase
from ellar.di import ProviderConfig, request_or_transient_scope
from ellar.utils.importer import get_main_directory_by_stack
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
)
from sqlalchemy.orm import Session

from ellar_sql.services import EllarSQLService

from .cli import DBCommands
from .schemas import MigrationOption, SQLAlchemyConfig


def _invalid_configuration(message: str) -> t.Callable:
    def _raise_exception():
        raise RuntimeError(message)

    return _raise_exception


async def _session_cleanup(
    db_service: EllarSQLService, session: t.Union[Session, AsyncSession]
) -> None:
    res = session.close()
    if isinstance(res, t.Coroutine):
        await res

    res = db_service.session_factory.remove()
    if isinstance(res, t.Coroutine):
        await res


@as_middleware
async def session_middleware(
    context: IHostContext, call_next: t.Callable[..., t.Coroutine]
):
    connection = context.switch_to_http_connection().get_client()

    db_service = context.get_service_provider().get(EllarSQLService)
    session = db_service.session_factory()

    connection.state.session = session

    try:
        await call_next()
    finally:
        await _session_cleanup(db_service, session)


@Module(
    commands=[DBCommands],
    exports=[
        EllarSQLService,
        Session,
        AsyncSession,
        AsyncEngine,
        sa.Engine,
        MigrationOption,
    ],
    providers=[EllarSQLService],
    name="EllarSQL",
)
class EllarSQLModule(ModuleBase, IModuleSetup):
    @classmethod
    def post_build(cls, module_ref: "ModuleRefBase") -> None:
        module_ref.config.MIDDLEWARE = list(module_ref.config.MIDDLEWARE) + [
            session_middleware
        ]

    @classmethod
    def setup(
        cls,
        *,
        databases: t.Union[str, t.Dict[str, t.Any]],
        migration_options: t.Union[t.Dict[str, t.Any], MigrationOption],
        session_options: t.Optional[t.Dict[str, t.Any]] = None,
        engine_options: t.Optional[t.Dict[str, t.Any]] = None,
        models: t.Optional[t.List[str]] = None,
        echo: bool = False,
        root_path: t.Optional[str] = None,
    ) -> "DynamicModule":
        """
        Configures EllarSQLModule and setup required providers.
        """
        root_path = root_path or get_main_directory_by_stack("__main__", stack_level=2)
        if isinstance(migration_options, MigrationOption):
            migration_options = migration_options.dict()
        migration_options.setdefault("directory", "migrations")
        schema = SQLAlchemyConfig.model_validate(
            {
                "databases": databases,
                "engine_options": engine_options,
                "echo": echo,
                "models": models,
                "session_options": session_options,
                "migration_options": migration_options,
                "root_path": root_path,
            },
            from_attributes=True,
        )
        return cls.__setup_module(schema)

    @classmethod
    def __setup_module(cls, sql_alchemy_config: SQLAlchemyConfig) -> DynamicModule:
        db_service = EllarSQLService(
            databases=sql_alchemy_config.databases,
            common_engine_options=sql_alchemy_config.engine_options,
            common_session_options=sql_alchemy_config.session_options,
            echo=sql_alchemy_config.echo,
            models=sql_alchemy_config.models,
            root_path=sql_alchemy_config.root_path,
            migration_options=sql_alchemy_config.migration_options,
        )
        providers: t.List[t.Any] = []

        if db_service.has_async_engine_driver:
            providers.append(ProviderConfig(AsyncEngine, use_value=db_service.engine))
            providers.append(
                ProviderConfig(
                    AsyncSession,
                    use_value=lambda: db_service.session_factory(),
                    scope=request_or_transient_scope,
                )
            )
            providers.append(
                ProviderConfig(
                    Session,
                    use_value=_invalid_configuration(
                        f"{Session} is not configured based on your database options. Please use {AsyncSession}"
                    ),
                    scope=request_or_transient_scope,
                )
            )
            providers.append(
                ProviderConfig(
                    sa.Engine,
                    use_value=_invalid_configuration(
                        f"{sa.Engine} is not configured based on your database options. Please use {AsyncEngine}"
                    ),
                    scope=request_or_transient_scope,
                )
            )
        else:
            providers.append(ProviderConfig(sa.Engine, use_value=db_service.engine))
            providers.append(
                ProviderConfig(
                    Session,
                    use_value=lambda: db_service.session_factory(),
                    scope=request_or_transient_scope,
                )
            )
            providers.append(
                ProviderConfig(
                    AsyncSession,
                    use_value=_invalid_configuration(
                        f"{AsyncSession} is not configured based on your database options. Please use {Session}"
                    ),
                    scope=request_or_transient_scope,
                )
            )
            providers.append(
                ProviderConfig(
                    AsyncEngine,
                    use_value=_invalid_configuration(
                        f"{AsyncEngine} is not configured based on your database options. Please use {sa.Engine}"
                    ),
                    scope=request_or_transient_scope,
                )
            )

        providers.append(ProviderConfig(EllarSQLService, use_value=db_service))
        providers.append(
            ProviderConfig(
                MigrationOption, use_value=lambda: db_service.migration_options
            )
        )

        return DynamicModule(
            cls,
            providers=providers,
        )

    @classmethod
    def register_setup(cls, **override_config: t.Any) -> ModuleSetup:
        """
        Register Module to be configured through `SQLALCHEMY_CONFIG` variable in Application Config
        """
        root_path = get_main_directory_by_stack("__main__", stack_level=2)
        return ModuleSetup(
            cls,
            inject=[Config],
            factory=functools.partial(
                cls.__register_setup_factory,
                root_path=root_path,
                override_config=override_config,
            ),
        )

    @staticmethod
    def __register_setup_factory(
        module_ref: ModuleRefBase,
        config: Config,
        root_path: str,
        override_config: t.Dict[str, t.Any],
    ) -> DynamicModule:
        if config.get("ELLAR_SQL") and isinstance(config.ELLAR_SQL, dict):
            defined_config = dict(config.ELLAR_SQL)
            defined_config.update(override_config)
            defined_config.setdefault("root_path", root_path)

            schema = SQLAlchemyConfig.model_validate(
                defined_config, from_attributes=True
            )

            schema.migration_options.directory = get_main_directory_by_stack(
                schema.migration_options.directory,
                stack_level=0,
                from_dir=defined_config["root_path"],
            )
            module = t.cast(t.Type["EllarSQLModule"], module_ref.module)

            return module.__setup_module(schema)
        raise RuntimeError("Could not find `ELLAR_SQL` in application config.")
