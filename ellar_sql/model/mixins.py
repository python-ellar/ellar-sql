import typing as t

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from pydantic.v1 import BaseModel

from ellar_sql.constant import ABSTRACT_KEY, DATABASE_KEY, DEFAULT_KEY, TABLE_KEY
from ellar_sql.model.utils import (
    camel_to_snake_case,
    make_metadata,
    should_set_table_name,
)
from ellar_sql.schemas import ModelBaseConfig, ModelMetaStore


class asss(BaseModel):
    sd: str


IncEx = t.Union[t.Set[int], t.Set[str], t.Dict[int, t.Any], t.Dict[str, t.Any]]

if t.TYPE_CHECKING:
    from .base import ModelBase

__ellar_sqlalchemy_models__: t.Dict[str, t.Type["ModelBase"]] = {}


def get_registered_models() -> t.Dict[str, t.Type["ModelBase"]]:
    return __ellar_sqlalchemy_models__.copy()


class NameMixin:
    metadata: sa.MetaData
    __tablename__: str
    __table__: sa.Table

    def __init_subclass__(cls, **kwargs: t.Dict[str, t.Any]) -> None:
        if should_set_table_name(cls):
            cls.__tablename__ = camel_to_snake_case(cls.__name__)

        super().__init_subclass__(**kwargs)


class DatabaseBindKeyMixin:
    metadata: sa.MetaData

    def __init_subclass__(cls, **kwargs: t.Dict[str, t.Any]) -> None:
        if not ("metadata" in cls.__dict__ or TABLE_KEY in cls.__dict__) and hasattr(
            cls, DATABASE_KEY
        ):
            database_bind_key = getattr(cls, DATABASE_KEY, DEFAULT_KEY)
            parent_metadata = getattr(cls, "metadata", None)
            db_metadata = make_metadata(database_bind_key)

            if db_metadata.metadata is not parent_metadata:
                cls.metadata = db_metadata.metadata
                cls.registry = db_metadata.registry  # type:ignore[attr-defined]

        super().__init_subclass__(**kwargs)


class ModelTrackMixin:
    metadata: sa.MetaData
    __mms__: ModelMetaStore
    __table__: sa.Table

    def __init_subclass__(cls, **kwargs: t.Dict[str, t.Any]) -> None:
        options: ModelBaseConfig = kwargs.pop(  # type:ignore[assignment]
            "options",
            ModelBaseConfig(as_base=False, use_bases=[sa_orm.DeclarativeBase]),
        )

        super().__init_subclass__(**kwargs)

        if TABLE_KEY in cls.__dict__ and ABSTRACT_KEY not in cls.__dict__:
            __ellar_sqlalchemy_models__[str(cls)] = cls  # type:ignore[assignment]

            cls.__mms__ = ModelMetaStore(
                base_config=options,
                pk_column=None,
                columns=list(cls.__table__.columns),  # type:ignore[arg-type]
            )


class ModelDataExportMixin:
    __mms__: t.Optional[ModelMetaStore] = None

    def __repr__(self) -> str:
        state = sa.inspect(self)
        assert state is not None

        if state.transient:
            pk = f"(transient {id(self)})"
        elif state.pending:
            pk = f"(pending {id(self)})"
        else:
            pk = ", ".join(map(str, state.identity))

        return f"<{type(self).__name__} {pk}>"

    def _calculate_keys(
        self,
        include: t.Optional[t.Set[str]],
        exclude: t.Optional[t.Set[str]],
    ) -> t.Set[str]:
        keys: t.Set[str] = {k for k in self.__dict__.keys() if not k.startswith("_sa")}

        if include is None and exclude is None:
            return keys

        if include is not None:
            keys &= include

        if exclude:
            keys -= exclude

        return keys

    def _iter(
        self,
        include: t.Optional[t.Set[str]],
        exclude: t.Optional[t.Set[str]],
        exclude_none: bool = False,
    ) -> t.Generator[t.Tuple[str, t.Any], None, None]:
        allowed_keys = self._calculate_keys(include=include, exclude=exclude)

        for field_key, v in self.__dict__.items():
            if (allowed_keys is not None and field_key not in allowed_keys) or (
                exclude_none and v is None
            ):
                continue
            yield field_key, v

    def dict(
        self,
        include: t.Optional[t.Set[str]] = None,
        exclude: t.Optional[t.Set[str]] = None,
        exclude_none: bool = False,
    ) -> t.Dict[str, t.Any]:
        # TODO: implement advance exclude and include that goes deep into relationships too
        return dict(
            self._iter(include=include, exclude_none=exclude_none, exclude=exclude)
        )
