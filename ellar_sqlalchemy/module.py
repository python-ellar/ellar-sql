import functools
import typing as t

import sqlalchemy as sa
from ellar.app import current_injector
from ellar.common import IApplicationShutdown, IModuleSetup, Module
from ellar.common.utils.importer import get_main_directory_by_stack
from ellar.core import Config, DynamicModule, ModuleBase, ModuleSetup
from ellar.di import ProviderConfig, request_scope
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
)
from sqlalchemy.orm import Session

from ellar_sqlalchemy.services import EllarSQLAlchemyService

from .cli import DBCommands
from .schemas import MigrationOption, SQLAlchemyConfig


@Module(commands=[DBCommands])
class EllarSQLAlchemyModule(ModuleBase, IModuleSetup, IApplicationShutdown):
    async def on_shutdown(self) -> None:
        db_service = current_injector.get(EllarSQLAlchemyService)
        db_service.session_factory.remove()

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
    ) -> "DynamicModule":
        """
        Configures EllarSQLAlchemyModule and setup required providers.
        """
        root_path = get_main_directory_by_stack("__main__", stack_level=2)
        if isinstance(migration_options, dict):
            migration_options.update(
                directory=get_main_directory_by_stack(
                    migration_options.get("directory", "__main__/migrations"),
                    stack_level=2,
                    from_dir=root_path,
                )
            )
        if isinstance(migration_options, MigrationOption):
            migration_options.directory = get_main_directory_by_stack(
                migration_options.directory, stack_level=2, from_dir=root_path
            )
            migration_options = migration_options.dict()

        schema = SQLAlchemyConfig.model_validate(
            {
                "databases": databases,
                "engine_options": engine_options,
                "echo": echo,
                "models": models,
                "migration_options": migration_options,
                "root_path": root_path,
            },
            from_attributes=True,
        )
        return cls.__setup_module(schema)

    @classmethod
    def __setup_module(cls, sql_alchemy_config: SQLAlchemyConfig) -> DynamicModule:
        db_service = EllarSQLAlchemyService(
            databases=sql_alchemy_config.databases,
            common_engine_options=sql_alchemy_config.engine_options,
            common_session_options=sql_alchemy_config.session_options,
            echo=sql_alchemy_config.echo,
            models=sql_alchemy_config.models,
            root_path=sql_alchemy_config.root_path,
            migration_options=sql_alchemy_config.migration_options,
        )
        providers: t.List[t.Any] = []

        if db_service._async_session_type:
            providers.append(ProviderConfig(AsyncEngine, use_value=db_service.engine))
            providers.append(
                ProviderConfig(
                    AsyncSession,
                    use_value=lambda: db_service.session_factory(),
                    scope=request_scope,
                )
            )
        else:
            providers.append(ProviderConfig(sa.Engine, use_value=db_service.engine))
            providers.append(
                ProviderConfig(
                    Session,
                    use_value=lambda: db_service.session_factory(),
                    scope=request_scope,
                )
            )

        providers.append(ProviderConfig(EllarSQLAlchemyService, use_value=db_service))
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
        module: t.Type["EllarSQLAlchemyModule"],
        config: Config,
        root_path: str,
        override_config: t.Dict[str, t.Any],
    ) -> DynamicModule:
        if config.get("SQLALCHEMY_CONFIG") and isinstance(
            config.SQLALCHEMY_CONFIG, dict
        ):
            defined_config = dict(config.SQLALCHEMY_CONFIG, root_path=root_path)
            defined_config.update(override_config)

            schema = SQLAlchemyConfig.model_validate(
                defined_config, from_attributes=True
            )

            schema.migration_options.directory = get_main_directory_by_stack(
                schema.migration_options.directory, stack_level=2, from_dir=root_path
            )

            return module.__setup_module(schema)
        raise RuntimeError("Could not find `SQLALCHEMY_CONFIG` in application config.")
