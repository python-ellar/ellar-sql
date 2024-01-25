import functools
import logging
import typing as t

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine

from ellar_sql.model.database_binds import get_metadata
from ellar_sql.types import RevisionArgs

from .base import AlembicEnvMigrationBase

if t.TYPE_CHECKING:
    from alembic.operations import MigrationScript
    from alembic.runtime.environment import EnvironmentContext
    from alembic.runtime.migration import MigrationContext


logger = logging.getLogger("alembic.env")


class SingleDatabaseAlembicEnvMigration(AlembicEnvMigrationBase):
    """
    Migration Class for a Single Database Configuration
    for both asynchronous and synchronous database engine dialect
    """

    def default_process_revision_directives(
        self,
        context: "MigrationContext",
        revision: RevisionArgs,
        directives: t.List["MigrationScript"],
    ) -> None:
        if getattr(context.config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    def run_migrations_offline(
        self, context: "EnvironmentContext"
    ) -> None:  # pragma:no cover
        """Run migrations in 'offline' mode.

        This configures the context with just a URL
        and not an Engine, though an Engine is acceptable
        here as well.  By skipping the Engine creation
        we don't even need a DBAPI to be available.

        Calls to context.execute() here emit the given string to the
        script output.

        """

        key, engine = self.db_service.engines.popitem()
        metadata = get_metadata(key, certain=True).metadata

        conf_args = self.get_user_context_configurations()

        context.configure(
            url=str(engine.url).replace("%", "%%"),
            target_metadata=metadata,
            literal_binds=True,
            **conf_args,
        )

        with context.begin_transaction():
            context.run_migrations()

    def _migration_action(
        self,
        connection: sa.Connection,
        metadata: sa.MetaData,
        context: "EnvironmentContext",
    ) -> None:
        # this callback is used to prevent an auto-migration from being generated
        # when there are no changes to the schema
        # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
        conf_args = self.get_user_context_configurations()
        conf_args.setdefault(
            "process_revision_directives", self.default_process_revision_directives
        )

        context.configure(connection=connection, target_metadata=metadata, **conf_args)

        with context.begin_transaction():
            context.run_migrations()

    async def run_migrations_online(self, context: "EnvironmentContext") -> None:
        """Run migrations in 'online' mode.

        In this scenario we need to create an Engine
        and associate a connection with the context.

        """

        key, engine = self.db_service.engines.popitem()
        metadata = get_metadata(key, certain=True).metadata

        migration_action_partial = functools.partial(
            self._migration_action, metadata=metadata, context=context
        )

        if engine.dialect.is_async:
            async_engine = AsyncEngine(engine)
            async with async_engine.connect() as connection:
                await connection.run_sync(migration_action_partial)
        else:
            with engine.connect() as connection:
                migration_action_partial(connection)
