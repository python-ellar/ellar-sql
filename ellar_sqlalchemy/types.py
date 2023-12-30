import typing as t

if t.TYPE_CHECKING:
    from alembic.operations import MigrationScript
    from alembic.runtime.migration import MigrationContext

RevisionArgs = t.Union[
    str,
    t.Iterable[t.Optional[str]],
    t.Iterable[str],
]

RevisionDirectiveCallable = t.Callable[
    ["MigrationContext", RevisionArgs, t.List["MigrationScript"]], None
]
