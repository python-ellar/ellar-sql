import typing as t

import sqlalchemy as sa

__model_database_metadata__: t.Dict[str, sa.MetaData] = {}


def update_database_binds(key: str, value: sa.MetaData) -> None:
    __model_database_metadata__[key] = value


def get_database_binds() -> t.Dict[str, sa.MetaData]:
    return __model_database_metadata__.copy()


def get_database_bind(key: str, certain: bool = False) -> sa.MetaData:
    if certain:
        return __model_database_metadata__[key]
    return __model_database_metadata__.get(key)  # type:ignore[return-value]


def has_database_bind(key: str) -> bool:
    return key in __model_database_metadata__
