import typing as t
from logging.config import fileConfig

from alembic import context
from ellar.app import current_injector
from ellar.threading import execute_coroutine_with_sync_worker

from ellar_sqlalchemy.migrations import (
    MultipleDatabaseAlembicEnvMigration,
    SingleDatabaseAlembicEnvMigration,
)
from ellar_sqlalchemy.services import EllarSQLAlchemyService

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)  # type:ignore[arg-type]

# logger = logging.getLogger("alembic.env")
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


async def main() -> None:
    db_service: EllarSQLAlchemyService = current_injector.get(EllarSQLAlchemyService)

    alembic_env_migration_klass: t.Type[
        t.Union[MultipleDatabaseAlembicEnvMigration, SingleDatabaseAlembicEnvMigration]
    ]

    if len(db_service.engines) > 1:
        alembic_env_migration_klass = MultipleDatabaseAlembicEnvMigration
    else:
        alembic_env_migration_klass = SingleDatabaseAlembicEnvMigration

    # initialize migration class
    alembic_env_migration = alembic_env_migration_klass(db_service)

    if context.is_offline_mode():
        alembic_env_migration.run_migrations_offline(context)  # type:ignore[arg-type]
    else:
        await alembic_env_migration.run_migrations_online(context)  # type:ignore[arg-type]


execute_coroutine_with_sync_worker(main())
