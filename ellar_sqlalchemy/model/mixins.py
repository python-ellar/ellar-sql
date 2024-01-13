import typing as t

import sqlalchemy as sa

from ellar_sqlalchemy.constant import ABSTRACT_KEY, DATABASE_KEY, DEFAULT_KEY, TABLE_KEY

from .utils import camel_to_snake_case, make_metadata, should_set_table_name

if t.TYPE_CHECKING:
    from .base import ModelBase

__ellar_sqlalchemy_models__: t.Dict[str, t.Type["ModelBase"]] = {}


def get_registered_models() -> t.Dict[str, t.Type["ModelBase"]]:
    return __ellar_sqlalchemy_models__.copy()


#
# def __name_mixin__(cls: t.Type, *args:t.Any, is_subclass:bool=False, **kwargs:t.Any) -> None:
#     if should_set_table_name(cls) and not kwargs.get('__skip_mixins__'):
#         cls.__tablename__ = camel_to_snake_case(cls.__name__)
#
#     if is_subclass:
#         super(NameMixin, cls).__init_subclass__(**kwargs)
#     else:
#         super(NameMetaMixin, cls).__init__(*args, **kwargs)
#
#
# def __database_key_bind__(cls: t.Type, *args: t.Any, is_subclass: bool = False, **kwargs: t.Any) -> None:
#     if not ("metadata" in cls.__dict__ or TABLE_KEY in cls.__dict__) and hasattr(
#             cls, DATABASE_KEY
#     ) and not kwargs.get('__skip_mixins__'):
#         database_bind_key = getattr(cls, DATABASE_KEY, DEFAULT_KEY)
#         parent_metadata = getattr(cls, "metadata", None)
#         metadata = make_metadata(database_bind_key)
#
#         if metadata is not parent_metadata:
#             cls.metadata = metadata
#     if is_subclass:
#         super(DatabaseBindKeyMixin, cls).__init_subclass__(**kwargs)
#     else:
#         super(DatabaseBindKeyMetaMixin, cls).__init__(*args, **kwargs)
#
#
# def __model_track__(cls: t.Type, *args: t.Any, is_subclass: bool = False, **kwargs: t.Any) -> None:
#     if is_subclass:
#         super(ModelTrackMixin, cls).__init_subclass__(**kwargs)
#     else:
#         super(ModelTrackMetaMixin, cls).__init__(*args, **kwargs)
#
#     if TABLE_KEY in cls.__dict__ and ABSTRACT_KEY not in cls.__dict__  and not kwargs.get('__skip_mixins__'):
#         __ellar_sqlalchemy_models__[str(cls)] = cls  # type:ignore[assignment]
#
#
# NameMixin = types.new_class(
#     "NameMixin", (), {},
#     lambda ns: ns.update({"__init_subclass__": lambda cls, **kw: __name_mixin__(cls, **kw, is_subclass=True)})
# )
#
# NameMetaMixin = types.new_class(
#     "NameMixin", (type, ), {},
#     lambda ns: ns.update({"__init__": __name_mixin__})
# )
#
# DatabaseBindKeyMixin = types.new_class(
#     "DatabaseBindKeyMixin", (), {},
#     lambda ns: ns.update({"__init_subclass__": lambda cls, **kw: __database_key_bind__(cls, **kw, is_subclass=True)})
# )
#
# DatabaseBindKeyMetaMixin = types.new_class(
#     "DatabaseBindKeyMetaMixin", (type,), {},
#     lambda ns: ns.update({"__init__": __database_key_bind__})
# )
#
# ModelTrackMixin = types.new_class(
#     "ModelTrackMixin", (), {},
#     lambda ns: ns.update({"__init_subclass__": lambda cls, **kw: __model_track__(cls, **kw, is_subclass=True)})
# )
#
# ModelTrackMetaMixin = types.new_class(
#     "ModelTrackMetaMixin", (type,), {},
#     lambda ns: ns.update({"__init__": __model_track__})
# )
#
#
# class DefaultBaseMeta(DatabaseBindKeyMetaMixin, NameMetaMixin, ModelTrackMetaMixin, type(DeclarativeBase)):
#     pass


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
    __dnd__ = "Ellar"

    def __init_subclass__(cls, **kwargs: t.Dict[str, t.Any]) -> None:
        if not ("metadata" in cls.__dict__ or TABLE_KEY in cls.__dict__) and hasattr(
            cls, DATABASE_KEY
        ):
            database_bind_key = getattr(cls, DATABASE_KEY, DEFAULT_KEY)
            parent_metadata = getattr(cls, "metadata", None)
            metadata = make_metadata(database_bind_key)

            if metadata is not parent_metadata:
                cls.metadata = metadata

        super().__init_subclass__(**kwargs)


class ModelTrackMixin:
    metadata: sa.MetaData

    def __init_subclass__(cls, **kwargs: t.Dict[str, t.Any]) -> None:
        super().__init_subclass__(**kwargs)

        if TABLE_KEY in cls.__dict__ and ABSTRACT_KEY not in cls.__dict__:
            __ellar_sqlalchemy_models__[str(cls)] = cls  # type:ignore[assignment]


class ModelDataExportMixin:
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

    def dict(self, exclude: t.Optional[t.Set[str]] = None) -> t.Dict[str, t.Any]:
        # TODO: implement advance exclude and include that goes deep into relationships too
        _exclude: t.Set[str] = set() if not exclude else exclude

        tuple_generator = (
            (k, v)
            for k, v in self.__dict__.items()
            if k not in _exclude and not k.startswith("_sa")
        )
        return dict(tuple_generator)
