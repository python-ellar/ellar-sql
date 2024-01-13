import types
import typing as t

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from ellar.app import current_injector
from sqlalchemy.ext.asyncio import AsyncSession

from ellar_sqlalchemy.constant import DATABASE_BIND_KEY, DATABASE_KEY, DEFAULT_KEY
from ellar_sqlalchemy.schemas import ModelBaseConfig

from .database_binds import get_database_bind, has_database_bind, update_database_binds
from .mixins import (
    DatabaseBindKeyMixin,
    ModelDataExportMixin,
    ModelTrackMixin,
    NameMixin,
)


def _update_metadata(namespace: t.Dict[str, t.Any]) -> None:
    database_key = namespace.get(DATABASE_KEY, DEFAULT_KEY)
    metadata = namespace.get("metadata", None)

    if metadata and database_key:
        if not has_database_bind(database_key):
            # verify the key exist and store the metadata
            metadata.info[DATABASE_BIND_KEY] = database_key
            update_database_binds(database_key, metadata)
        # if we have saved metadata then, its save to remove it and allow
        # DatabaseBindKeyMixin to set it back when the class if fully created.
        namespace.pop("metadata")


def _get_declarative_bases(
    bases: t.Sequence[t.Any],
) -> t.List[t.Type[t.Union[sa_orm.DeclarativeBase, sa_orm.DeclarativeBaseNoMeta]]]:
    declarative_bases = [
        b
        for b in bases
        if issubclass(b, (sa_orm.DeclarativeBase, sa_orm.DeclarativeBaseNoMeta))
    ]
    return declarative_bases


class ModelMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: t.Tuple[t.Any, ...],
        namespace: t.Dict[str, t.Any],
        **kwargs: t.Any,
    ) -> t.Type[t.Union["Model", t.Any]]:
        if bases == (ModelBase,) and name == "Model":
            return type.__new__(mcs, name, bases, namespace, **kwargs)

        options = namespace.pop(
            "__base_config__",
            ModelBaseConfig(
                make_declarative_base=False, use_bases=[sa_orm.DeclarativeBase]
            ),
        )
        if isinstance(options, dict):
            options = ModelBaseConfig(**options)
        assert isinstance(
            options, ModelBaseConfig
        ), f"{options.__class__} is not a support ModelMetaOptions"

        if options.make_declarative_base:
            declarative_bases = _get_declarative_bases(options.use_bases)
            working_base = list(bases)

            has_declarative_bases = any(_get_declarative_bases(working_base))

            working_base.extend(options.use_bases)
            working_base = [
                base for base in working_base if base not in [Model, object]
            ]

            if len(declarative_bases) > 1:
                # raise error if more than one declarative base is found
                raise ValueError(
                    "Only one declarative base can be passed to SQLAlchemy."
                    " Got: {}".format(options.use_bases)
                )
            _update_metadata(namespace)

            mixin_classes = [
                mixin
                for mixin in [
                    DatabaseBindKeyMixin,
                    NameMixin,
                    ModelTrackMixin,
                    ModelBase,
                ]
                if mixin not in working_base
            ]

            if len(declarative_bases) == 0:
                if not has_declarative_bases:
                    working_base.append(sa_orm.DeclarativeBase)

                declarative_bases.append(sa_orm.DeclarativeBase)

            model = types.new_class(
                name,
                (*mixin_classes, *working_base),
                {"metaclass": type(declarative_bases[0])},
                lambda ns: ns.update(namespace),
            )

            if not has_database_bind(DEFAULT_KEY):
                # Use the model's metadata as the default metadata.
                model.metadata.info[DATABASE_BIND_KEY] = DEFAULT_KEY
                update_database_binds(DEFAULT_KEY, model.metadata)
            elif not has_database_bind(model.metadata.info.get(DATABASE_BIND_KEY)):
                # Use the passed in default metadata as the model's metadata.
                model.metadata = get_database_bind(DEFAULT_KEY, certain=True)

            return model

        # _update_metadata(namespace)

        base = ModelMeta(
            "ModelBase",
            bases,
            {
                "__base_config__": ModelBaseConfig(
                    use_bases=options.use_bases, make_declarative_base=True
                )
            },
        )

        return types.new_class(name, (base,), {}, lambda ns: ns.update(namespace))


class ModelBase(ModelDataExportMixin):
    __database__: str = "default"

    if t.TYPE_CHECKING:
        _sa_registry: t.ClassVar[sa_orm.registry]

        registry: t.ClassVar[sa_orm.registry]

        metadata: t.ClassVar[sa.MetaData]

        __name__: t.ClassVar[str]

        __mapper__: t.ClassVar[sa_orm.Mapper[t.Any]]

        __table__: t.ClassVar[sa.Table]

        __tablename__: t.Any

        __mapper_args__: t.Any

        __table_args__: t.Any

        def __init__(self, **kwargs: t.Any) -> None:
            ...

        def dict(self, exclude: t.Optional[t.Set[str]] = None) -> t.Dict[str, t.Any]:
            ...

        def _sa_inspect_type(self) -> sa.Mapper["ModelBase"]:
            ...

        def _sa_inspect_instance(self) -> sa.InstanceState["ModelBase"]:
            ...

    @classmethod
    def get_db_session(
        cls,
    ) -> t.Union[sa_orm.Session, AsyncSession, t.Any]:
        from ellar_sqlalchemy.services import EllarSQLAlchemyService

        db_service = current_injector.get(EllarSQLAlchemyService)
        return db_service.session_factory()


class Model(ModelBase, metaclass=ModelMeta):
    __base_config__: t.Union[ModelBaseConfig, t.Dict[str, t.Any]]
