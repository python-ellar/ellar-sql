# **Alembic Env**

In the generated migration template, EllarSQL adopts an async-first approach for handling migration file generation. 
This approach simplifies the execution of migrations for both `Session`, `Engine`, `AsyncSession`, and `AsyncEngine`, 
but it also introduces a certain level of complexity.

```python
from logging.config import fileConfig

from alembic import context
from ellar.app import current_injector
from ellar.threading import execute_coroutine_with_sync_worker

from ellar_sql.migrations import SingleDatabaseAlembicEnvMigration
from ellar_sql.services import EllarSQLService

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
    db_service: EllarSQLService = current_injector.get(EllarSQLService)

    # initialize migration class
    alembic_env_migration = SingleDatabaseAlembicEnvMigration(db_service)

    if context.is_offline_mode():
        alembic_env_migration.run_migrations_offline(context)  # type:ignore[arg-type]
    else:
        await alembic_env_migration.run_migrations_online(context)  # type:ignore[arg-type]


execute_coroutine_with_sync_worker(main())
```

The EllarSQL migration package provides two main migration classes:

- **SingleDatabaseAlembicEnvMigration**: Manages migrations for a **single** database configuration, catering to both `Engine` and `AsyncEngine`.
- **MultipleDatabaseAlembicEnvMigration**: Manages migrations for **multiple** database configurations, covering both `Engine` and `AsyncEngine`.

## **Customizing the Env file**

To customize or edit the Env file, it is recommended to inherit from either `SingleDatabaseAlembicEnvMigration` or `MultipleDatabaseAlembicEnvMigration` based on your specific configuration. Make the necessary changes within the inherited class.

If you prefer to write something from scratch, then the abstract class `AlembicEnvMigrationBase` is the starting point. This class includes three abstract methods and expects a `EllarSQLService` during initialization, as demonstrated below:

```python
class AlembicEnvMigrationBase:
    def __init__(self, db_service: EllarSQLService) -> None:
        self.db_service = db_service
        self.use_two_phase = db_service.migration_options.use_two_phase

    @abstractmethod
    def default_process_revision_directives(
        self,
        context: "MigrationContext",
        revision: RevisionArgs,
        directives: t.List["MigrationScript"],
    ) -> t.Any:
        pass

    @abstractmethod
    def run_migrations_offline(self, context: "EnvironmentContext") -> None:
        pass

    @abstractmethod
    async def run_migrations_online(self, context: "EnvironmentContext") -> None:
        pass
```

The `run_migrations_online` and `run_migrations_offline` are all similar to the same function from Alembic env.py template.
The `default_process_revision_directives` is a callback is used to prevent an auto-migration from being generated 
when there are no changes to the schema described in details [here](http://alembic.zzzcomputing.com/en/latest/cookbook.html)

### Example
```python
import logging
from logging.config import fileConfig

from alembic import context
from ellar_sql.migrations import AlembicEnvMigrationBase
from ellar_sql.model.database_binds import get_metadata
from ellar.app import current_injector
from ellar.threading import execute_coroutine_with_sync_worker
from ellar_sql.services import EllarSQLService

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
logger = logging.getLogger("alembic.env")
# Interpret the config file for Python logging.
# This line sets up loggers essentially.
fileConfig(config.config_file_name)  # type:ignore[arg-type]

class MyCustomMigrationEnv(AlembicEnvMigrationBase):
    def default_process_revision_directives(
        self,
        context,
        revision,
        directives,
    ) -> None:
        if getattr(context.config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    def run_migrations_offline(self, context: "EnvironmentContext") -> None:
        """Run migrations in 'offline' mode.

        This configures the context with just a URL
        and not an Engine, though an Engine is acceptable
        here as well.  By skipping the Engine creation
        we don't even need a DBAPI to be available.

        Calls to context.execute() here emit the given string to the
        script output.

        """
        pass

    async def run_migrations_online(self, context: "EnvironmentContext") -> None:
        """Run migrations in 'online' mode.

        In this scenario, we need to create an Engine
        and associate a connection with the context.

        """
        key, engine = self.db_service.engines.popitem()
        metadata = get_metadata(key, certain=True)

        conf_args = {}
        conf_args.setdefault(
            "process_revision_directives", self.default_process_revision_directives
        )

        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=metadata,
                **conf_args
            )
    
            with context.begin_transaction():
                context.run_migrations()

async def main() -> None:
    db_service: EllarSQLService = current_injector.get(EllarSQLService)

    # initialize migration class
    alembic_env_migration = MyCustomMigrationEnv(db_service)

    if context.is_offline_mode():
        alembic_env_migration.run_migrations_offline(context)
    else:
        await alembic_env_migration.run_migrations_online(context)

execute_coroutine_with_sync_worker(main())
```

This migration environment class, `MyCustomMigrationEnv`, inherits from `AlembicEnvMigrationBase` 
and provides the necessary methods for offline and online migrations. 
It utilizes the `EllarSQLService` to obtain the database engines and metadata for the migration process. 
The `main` function initializes and executes the migration class, with specific handling for offline and online modes.
