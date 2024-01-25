import os.path
import typing as t
from dataclasses import asdict, dataclass, field

import ellar.common as ecm
import sqlalchemy.orm as sa_orm
from pydantic import BaseModel, BeforeValidator, HttpUrl, TypeAdapter
from typing_extensions import Annotated

T = t.TypeVar("T")

Url = Annotated[
    str, BeforeValidator(lambda value: str(TypeAdapter(HttpUrl).validate_python(value)))
]


class BasePaginatedResponseSchema(BaseModel):
    count: int
    next: t.Optional[Url]
    previous: t.Optional[Url]
    results: t.List[t.Any]


class BasicPaginationSchema(BaseModel, t.Generic[T]):
    count: int
    items: t.List[T]


class PageNumberPaginationSchema(BaseModel, t.Generic[T]):
    count: int
    next: t.Optional[Url]
    previous: t.Optional[Url]
    items: t.List[T]


@dataclass
class ModelBaseConfig:
    # Will be used when creating SQLAlchemy Model as a base or standalone
    use_bases: t.Sequence[
        t.Union[
            t.Type[t.Union[sa_orm.DeclarativeBase, sa_orm.DeclarativeBaseNoMeta]],
            sa_orm.DeclarativeMeta,
            t.Any,
        ]
    ] = field(default_factory=lambda: [])
    # indicates whether a class should be created a base for other models to inherit
    as_base: bool = False
    _use: t.Optional[t.Type[t.Any]] = None

    # def get_use_type(self) -> t.Type[t.Any]:
    #     if not self._use:
    #         self._use = types.new_class("SQLAlchemyBase", tuple(self.use_bases), {})
    #     return self._use


@dataclass
class MigrationOption:
    directory: str
    use_two_phase: bool = False
    context_configure: t.Dict[str, t.Any] = field(default_factory=lambda: {})

    def dict(self) -> t.Dict[str, t.Any]:
        return asdict(self)

    def validate_directory(self, root_path: str) -> None:
        if not os.path.isabs(self.directory):
            self.directory = os.path.join(root_path, self.directory)


class SQLAlchemyConfig(ecm.Serializer):
    # model_config = {"arbitrary_types_allowed": True}

    databases: t.Union[str, t.Dict[str, t.Any]]
    migration_options: MigrationOption
    root_path: str

    session_options: t.Optional[t.Dict[str, t.Any]] = {
        "autoflush": False,
        "future": True,
        "expire_on_commit": False,
    }
    echo: bool = False
    engine_options: t.Optional[t.Dict[str, t.Any]] = None

    models: t.Optional[t.List[str]] = None


@dataclass
class ModelMetaStore:
    base_config: ModelBaseConfig
    pk_column: t.Optional[sa_orm.ColumnProperty] = None
    columns: t.List[sa_orm.ColumnProperty] = field(default_factory=lambda: [])

    def __post_init__(self) -> None:
        if self.columns:
            self.pk_column = next(c for c in self.columns if c.primary_key)

    @property
    def pk_name(self) -> t.Optional[str]:
        if self.pk_column is not None:
            return self.pk_column.key
        return None
