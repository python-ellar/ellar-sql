import typing as t

import sqlalchemy as sa
import sqlalchemy.sql.schema as sa_sql_schema

from ellar_sql.constant import DEFAULT_KEY
from ellar_sql.model.utils import make_metadata


class Table(sa.Table):
    """
    Custom SQLAlchemy Table class that supports database-binding
    E.g.:
    ```python
        from ellar_sql.model import Table

        user_book_m2m = Table(
            "user_book",
            sa.Column("user_id", sa.ForeignKey(User.id), primary_key=True),
            sa.Column("book_id", sa.ForeignKey(Book.id), primary_key=True),
            __database__='default'
        )
    ```
    """

    @t.overload
    def __init__(
        self,
        name: str,
        *args: sa_sql_schema.SchemaItem,
        __database__: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> None: ...

    @t.overload
    def __init__(
        self,
        name: str,
        metadata: sa.MetaData,
        *args: sa_sql_schema.SchemaItem,
        **kwargs: t.Any,
    ) -> None: ...

    @t.overload
    def __init__(
        self, name: str, *args: sa_sql_schema.SchemaItem, **kwargs: t.Any
    ) -> None: ...

    def __init__(
        self, name: str, *args: sa_sql_schema.SchemaItem, **kwargs: t.Any
    ) -> None:
        super().__init__(name, *args, **kwargs)  # type: ignore[arg-type]

    def __new__(
        cls, *args: t.Any, __database__: t.Optional[str] = None, **kwargs: t.Any
    ) -> "Table":
        # If a metadata arg is passed, go directly to the base Table. Also do
        # this for no args so the correct error is shown.
        if not args or (len(args) >= 2 and isinstance(args[1], sa.MetaData)):
            return super().__new__(cls, *args, **kwargs)

        db_metadata = make_metadata(__database__ or DEFAULT_KEY)
        return super().__new__(
            cls, *[args[0], db_metadata.metadata, *args[1:]], **kwargs
        )
