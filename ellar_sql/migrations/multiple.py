import logging
import typing as t
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from ellar_sql.model.database_binds import get_metadata
from ellar_sql.types import RevisionArgs

from .base import AlembicEnvMigrationBase

if t.TYPE_CHECKING:
    from alembic.operations import MigrationScript
    from alembic.runtime.environment import EnvironmentContext
    from alembic.runtime.migration import MigrationContext


logger = logging.getLogger("alembic.env")


@dataclass
class DatabaseInfo:
    name: str
    metadata: sa.MetaData
    engine: t.Union[sa.Engine, AsyncEngine]
    connection: t.Union[sa.Connection, AsyncConnection]
    use_two_phase: bool = False

    _transaction: t.Optional[t.Union[sa.TwoPhaseTransaction, sa.RootTransaction]] = None
    _sync_connection: t.Optional[sa.Connection] = None

    def sync_connection(self) -> sa.Connection:
        if not self._sync_connection:
            self._sync_connection = getattr(
                self.connection, "sync_connection", self.connection
            )
        assert self._sync_connection is not None
        return self._sync_connection

    def get_transactions(self) -> t.Union[sa.TwoPhaseTransaction, sa.RootTransaction]:
        if not self._transaction:
            if self.use_two_phase:
                self._transaction = self.sync_connection().begin_twophase()
            else:
                self._transaction = self.sync_connection().begin()
        assert self._transaction is not None
        return self._transaction


class MultipleDatabaseAlembicEnvMigration(AlembicEnvMigrationBase):
    """
    Migration Class for Multiple Database Configuration
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

            if len(script.upgrade_ops_list) == len(self.db_service.engines.keys()):
                # wait till there is a full check of all databases before removing empty operations

                for upgrade_ops in list(script.upgrade_ops_list):
                    if upgrade_ops.is_empty():
                        script.upgrade_ops_list.remove(upgrade_ops)

                for downgrade_ops in list(script.downgrade_ops_list):
                    if downgrade_ops.is_empty():
                        script.downgrade_ops_list.remove(downgrade_ops)

                if (
                    len(script.upgrade_ops_list) == 0
                    and len(script.downgrade_ops_list) == 0
                ):
                    directives[:] = []
                    logger.info("No changes in schema detected.")

    def run_migrations_offline(
        self, context: "EnvironmentContext"
    ) -> None:  # pragma:no cover
        """Run migrations in 'offline' mode.

        This configures the context with just a URL
        and not an Engine, though an Engine is acceptable
        here as well.  By skipping the Engine creation,
        we don't even need a DBAPI to be available.

        Calls to context.execute() here emit the given string to the
        script output.

        """
        # for --sql use case, run migrations for each URL into
        # individual files.

        conf_args = self.get_user_context_configurations()

        for key, engine in self.db_service.engines.items():
            logger.info("Migrating database %s" % key)

            url = str(engine.url).replace("%", "%%")
            metadata = get_metadata(key, certain=True).metadata

            file_ = "%s.sql" % key
            logger.info("Writing output to %s" % file_)

            with open(file_, "w") as buffer:
                context.configure(
                    url=url,
                    output_buffer=buffer,
                    target_metadata=metadata,
                    literal_binds=True,
                    **conf_args,
                )
                with context.begin_transaction():
                    context.run_migrations(engine_name=key)

    def _migration_action(
        self, _: t.Any, db_infos: t.List[DatabaseInfo], context: "EnvironmentContext"
    ) -> None:
        # this callback is used to prevent an auto-migration from being generated
        # when there are no changes to the schema
        # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html

        conf_args = self.get_user_context_configurations()
        conf_args.setdefault(
            "process_revision_directives", self.default_process_revision_directives
        )

        try:
            for db_info in db_infos:
                context.configure(
                    connection=db_info.sync_connection(),
                    upgrade_token="%s_upgrades" % db_info.name,
                    downgrade_token="%s_downgrades" % db_info.name,
                    target_metadata=db_info.metadata,
                    **conf_args,
                )

                context.run_migrations(engine_name=db_info.name)

            if self.use_two_phase:
                for db_info in db_infos:
                    db_info.get_transactions().prepare()  # type:ignore[attr-defined]

            for db_info in db_infos:
                db_info.get_transactions().commit()

        except Exception as ex:
            for db_info in db_infos:
                db_info.get_transactions().rollback()

            logger.error(ex)
            raise ex
        finally:
            for db_info in db_infos:
                db_info.sync_connection().close()

    async def _check_if_coroutine(self, func: t.Any) -> t.Any:
        if isinstance(func, t.Coroutine):
            return await func
        return func

    async def _compute_engine_info(self) -> t.List[DatabaseInfo]:
        res = []

        for key, engine in self.db_service.engines.items():
            metadata = get_metadata(key, certain=True).metadata

            if engine.dialect.is_async:
                async_engine = AsyncEngine(engine)
                connection = async_engine.connect()
                connection = await connection.start()
                engine = async_engine  # type:ignore[assignment]
            else:
                connection = engine.connect()  # type:ignore[assignment]

            database_info = DatabaseInfo(
                engine=engine,
                metadata=metadata,
                connection=connection,
                name=key,
                use_two_phase=self.use_two_phase,
            )
            database_info.get_transactions()
            res.append(database_info)
        return res

    async def run_migrations_online(self, context: "EnvironmentContext") -> None:
        # for the direct-to-DB use case, start a transaction on all
        # engines, then run all migrations, then commit all transactions.

        database_infos = await self._compute_engine_info()
        async_db_info_filter = [
            db_info for db_info in database_infos if db_info.engine.dialect.is_async
        ]
        try:
            if len(async_db_info_filter) > 0:
                await async_db_info_filter[0].connection.run_sync(
                    self._migration_action, database_infos, context
                )
            else:
                self._migration_action(None, database_infos, context)
        finally:
            for database_info_ in database_infos:
                await self._check_if_coroutine(database_info_.connection.close())
