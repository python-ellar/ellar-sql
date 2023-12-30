import typing as t
from dataclasses import asdict, dataclass, field

import ellar.common as ecm

from ellar_sqlalchemy.types import RevisionDirectiveCallable


@dataclass
class MigrationOption:
    directory: str
    revision_directives_callbacks: t.List[RevisionDirectiveCallable] = field(
        default_factory=lambda: []
    )
    use_two_phase: bool = False

    def dict(self) -> t.Dict[str, t.Any]:
        return asdict(self)


class SQLAlchemyConfig(ecm.Serializer):
    model_config = {"arbitrary_types_allowed": True}

    databases: t.Union[str, t.Dict[str, t.Any]]
    migration_options: MigrationOption
    root_path: str

    session_options: t.Dict[str, t.Any] = {
        "autoflush": False,
        "future": True,
        "expire_on_commit": False,
    }
    echo: bool = False
    engine_options: t.Optional[t.Dict[str, t.Any]] = None

    models: t.Optional[t.List[str]] = None
