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
    use_bases: t.Sequence[
        t.Union[
            t.Type[t.Union[sa_orm.DeclarativeBase, sa_orm.DeclarativeBaseNoMeta]],
            sa_orm.DeclarativeMeta,
            t.Any,
        ]
    ] = field(default_factory=lambda: [])

    make_declarative_base: bool = False
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
