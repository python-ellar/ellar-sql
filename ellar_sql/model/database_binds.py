import typing as t

import sqlalchemy as sa

__model_database_metadata__: t.Dict[str, sa.MetaData] = {}

from ellar_sql.constant import DEFAULT_KEY


def update_database_metadata(database_key: str, value: sa.MetaData) -> None:
    """
    Update a metadata based on a database key
    """
    __model_database_metadata__[database_key] = value


def get_all_metadata() -> t.Dict[str, sa.MetaData]:
    """
    Get all metadata available in your application
    """
    return __model_database_metadata__.copy()


def get_metadata(database_key: str = DEFAULT_KEY, certain: bool = False) -> sa.MetaData:
    """
    Gets Metadata associated with a database key
    """
    if certain:
        return __model_database_metadata__[database_key]
    return __model_database_metadata__.get(database_key)  # type:ignore[return-value]


def has_metadata(database_key: str) -> bool:
    """
    Checks if a metadata exist for a database key
    """
    return database_key in __model_database_metadata__
