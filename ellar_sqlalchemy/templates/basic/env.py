import asyncio
import typing as t
from logging.config import fileConfig

from alembic import context
from ellar.app import current_injector

from ellar_sqlalchemy.migrations import (
    MultipleDatabaseAlembicEnvMigration,
    SingleDatabaseAlembicEnvMigration,
)
from ellar_sqlalchemy.services import EllarSQLAlchemyService

db_service: EllarSQLAlchemyService = current_injector.get(EllarSQLAlchemyService)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)  # type:ignore[arg-type]
# logger = logging.getLogger("alembic.env")


AlembicEnvMigrationKlass: t.Type[
    t.Union[MultipleDatabaseAlembicEnvMigration, SingleDatabaseAlembicEnvMigration]
] = (
    MultipleDatabaseAlembicEnvMigration
    if len(db_service.engines) > 1
    else SingleDatabaseAlembicEnvMigration
)


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


alembic_env_migration = AlembicEnvMigrationKlass(db_service)

if context.is_offline_mode():
    alembic_env_migration.run_migrations_offline(context)  # type:ignore[arg-type]
else:
    asyncio.get_event_loop().run_until_complete(
        alembic_env_migration.run_migrations_online(context)  # type:ignore[arg-type]
    )
