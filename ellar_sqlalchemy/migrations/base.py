import typing as t
from abc import abstractmethod

from alembic.runtime.environment import NameFilterType
from sqlalchemy.sql.schema import SchemaItem

from ellar_sqlalchemy.services import EllarSQLAlchemyService
from ellar_sqlalchemy.types import RevisionArgs

if t.TYPE_CHECKING:
    from alembic.operations import MigrationScript
    from alembic.runtime.environment import EnvironmentContext
    from alembic.runtime.migration import MigrationContext


class AlembicEnvMigrationBase:
    def __init__(self, db_service: EllarSQLAlchemyService) -> None:
        self.db_service = db_service
        self.use_two_phase = db_service.migration_options.use_two_phase

    def include_object(
        self,
        obj: SchemaItem,
        name: t.Optional[str],
        type_: NameFilterType,
        reflected: bool,
        compare_to: t.Optional[SchemaItem],
    ) -> bool:
        # If you want to ignore things like these, set the following as a class attribute
        # __table_args__ = {"info": {"skip_autogen": True}}
        if obj.info.get("skip_autogen", False):
            return False

        return True

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
