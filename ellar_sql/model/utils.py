import re
import typing as t
from io import BytesIO

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm

from ellar_sql.constant import DATABASE_BIND_KEY, DEFAULT_KEY, NAMING_CONVERSION

from .database_binds import get_metadata, has_metadata, update_database_metadata

KB = 1024
MB = 1024 * KB


def copy_stream(source: t.IO, target: t.IO, *, chunk_size: int = 16 * KB) -> int:  # type:ignore[type-arg]
    length = 0
    while 1:
        buf = source.read(chunk_size)
        if not buf:
            break
        length += len(buf)
        target.write(buf)
    return length


def get_length(source: t.IO) -> int:  # type:ignore[type-arg]
    buffer = BytesIO()
    return copy_stream(source, buffer)


def make_metadata(database_key: str) -> sa.MetaData:
    if has_metadata(database_key):
        return get_metadata(database_key, certain=True)

    if database_key != DEFAULT_KEY:
        # Copy the naming convention from the default metadata.
        naming_convention = make_metadata(DEFAULT_KEY).naming_convention
    else:
        naming_convention = NAMING_CONVERSION

    # Set the bind key in info to be used by session.get_bind.
    metadata = sa.MetaData(
        naming_convention=naming_convention, info={DATABASE_BIND_KEY: database_key}
    )
    update_database_metadata(database_key, metadata)
    return metadata


def camel_to_snake_case(name: str) -> str:
    """Convert a ``CamelCase`` name to ``snake_case``."""
    name = re.sub(r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))", r"_\1", name)
    return name.lower().lstrip("_")


def should_set_table_name(cls: type) -> bool:
    if (
        cls.__dict__.get("__abstract__", False)
        or (
            not issubclass(cls, (sa_orm.DeclarativeBase, sa_orm.DeclarativeBaseNoMeta))
            and not any(isinstance(b, sa_orm.DeclarativeMeta) for b in cls.__mro__[1:])
        )
        or any(
            (b is sa_orm.DeclarativeBase or b is sa_orm.DeclarativeBaseNoMeta)
            for b in cls.__bases__
        )
    ):
        return False

    for base in cls.__mro__:
        if "__tablename__" not in base.__dict__:
            continue

        if isinstance(base.__dict__["__tablename__"], sa_orm.declared_attr):
            return False

        return not (
            base is cls
            or base.__dict__.get("__abstract__", False)
            or not (
                isinstance(base, sa_orm.decl_api.DeclarativeAttributeIntercept)
                or issubclass(base, sa_orm.DeclarativeBaseNoMeta)
            )
        )

    return True
