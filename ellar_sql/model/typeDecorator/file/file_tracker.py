import typing as t

from ellar.app import current_injector
from ellar_storage import StorageService
from sqlalchemy import event, orm
from sqlalchemy_file.types import FileFieldSessionTracker


class ModifiedFileFieldSessionTracker(FileFieldSessionTracker):
    @classmethod
    def delete_files(cls, paths: t.Set[str], ctx: str) -> None:
        if len(paths) == 0:
            return

        storage_service = current_injector.get(StorageService)

        for path in paths:
            storage_service.delete(path)

    @classmethod
    def unsubscribe_defaults(cls) -> None:
        event.remove(
            orm.Mapper, "mapper_configured", FileFieldSessionTracker._mapper_configured
        )
        event.remove(
            orm.Mapper, "after_configured", FileFieldSessionTracker._after_configured
        )
        event.remove(orm.Session, "after_commit", FileFieldSessionTracker._after_commit)
        event.remove(
            orm.Session,
            "after_soft_rollback",
            FileFieldSessionTracker._after_soft_rollback,
        )

    @classmethod
    def setup(cls) -> None:
        cls.unsubscribe_defaults()
        event.listen(orm.Mapper, "mapper_configured", cls._mapper_configured)
        event.listen(orm.Mapper, "after_configured", cls._after_configured)
        event.listen(orm.Session, "after_commit", cls._after_commit)
        event.listen(orm.Session, "after_soft_rollback", cls._after_soft_rollback)
