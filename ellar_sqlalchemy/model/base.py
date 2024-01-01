import types
import typing as t

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from sqlalchemy.ext.asyncio import AsyncSession

from ellar_sqlalchemy.constant import (
    DATABASE_BIND_KEY,
    DEFAULT_KEY,
    NAMING_CONVERSION,
)

from .database_binds import get_database_bind, has_database_bind, update_database_binds
from .mixins import (
    DatabaseBindKeyMixin,
    ModelDataExportMixin,
    ModelTrackMixin,
    NameMetaMixin,
)

SQLAlchemyDefaultBase = None


def _model_as_base(
    name: str, bases: t.Tuple[t.Any, ...], namespace: t.Dict[str, t.Any]
) -> t.Type["Model"]:
    global SQLAlchemyDefaultBase

    if SQLAlchemyDefaultBase is None:
        declarative_bases = [
            b
            for b in bases
            if issubclass(b, (sa_orm.DeclarativeBase, sa_orm.DeclarativeBaseNoMeta))
        ]

        def get_session(cls: t.Type[Model]) -> None:
            raise Exception("EllarSQLAlchemyService is not ready")

        namespace.update(
            get_db_session=getattr(Model, "get_session", classmethod(get_session)),
            skip_default_base_check=True,
        )

        model = types.new_class(
            f"{name}",
            (
                DatabaseBindKeyMixin,
                NameMetaMixin,
                ModelTrackMixin,
                ModelDataExportMixin,
                Model,
                *declarative_bases,
                sa_orm.DeclarativeBase,
            ),
            {},
            lambda ns: ns.update(namespace),
        )
        model = t.cast(t.Type[Model], model)
        SQLAlchemyDefaultBase = model

        if not has_database_bind(DEFAULT_KEY):
            # Use the model's metadata as the default metadata.
            model.metadata.info[DATABASE_BIND_KEY] = DEFAULT_KEY
            update_database_binds(DEFAULT_KEY, model.metadata)
        else:
            # Use the passed in default metadata as the model's metadata.
            model.metadata = get_database_bind(DEFAULT_KEY, certain=True)
        return model
    else:
        return SQLAlchemyDefaultBase


class ModelMeta(type(sa_orm.DeclarativeBase)):  # type:ignore[misc]
    def __new__(
        mcs,
        name: str,
        bases: t.Tuple[t.Any, ...],
        namespace: t.Dict[str, t.Any],
        **kwargs: t.Any,
    ) -> t.Type[t.Union["Model", t.Any]]:
        if bases == () and name == "Model":
            return type.__new__(mcs, name, tuple(bases), namespace, **kwargs)

        if "as_base" in kwargs:
            return _model_as_base(name, bases, namespace)

        _bases = list(bases)

        skip_default_base_check = False
        if "skip_default_base_check" in namespace:
            skip_default_base_check = namespace.pop("skip_default_base_check")

        if not skip_default_base_check:
            if SQLAlchemyDefaultBase is None:
                # raise Exception(
                #     "EllarSQLAlchemy Default Declarative Base has not been configured."
                #     "\nPlease call `configure_model_declarative_base` before ORM Model construction"
                #     " or Use EllarSQLAlchemy Service"
                # )
                _model_as_base(
                    "SQLAlchemyDefaultBase",
                    (),
                    {
                        "skip_default_base_check": True,
                        "metadata": sa.MetaData(naming_convention=NAMING_CONVERSION),
                    },
                )
                _bases = [SQLAlchemyDefaultBase, *_bases]
            elif SQLAlchemyDefaultBase and SQLAlchemyDefaultBase not in _bases:
                _bases = [SQLAlchemyDefaultBase, *_bases]

        return super().__new__(mcs, name, (*_bases,), namespace, **kwargs)  # type:ignore[no-any-return]


class Model(metaclass=ModelMeta):
    __database__: str = "default"

    if t.TYPE_CHECKING:

        def __init__(self, **kwargs: t.Any) -> None:
            ...

        @classmethod
        def get_db_session(
            cls,
        ) -> t.Union[sa_orm.Session, AsyncSession, t.Any]:
            ...

        def dict(self, exclude: t.Optional[t.Set[str]] = None) -> t.Dict[str, t.Any]:
            ...
