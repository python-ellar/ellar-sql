"""Ellar SQLAlchemy Module - Adds support for SQLAlchemy and Alembic package to your Ellar web Framework"""

__version__ = "0.0.1"

from .module import EllarSQLModule
from .pagination import LimitOffsetPagination, PageNumberPagination, paginate
from .query import (
    first_or_404,
    first_or_404_async,
    get_or_404,
    get_or_404_async,
    one_or_404,
    one_or_404_async,
)
from .schemas import MigrationOption, SQLAlchemyConfig
from .services import EllarSQLService

__all__ = [
    "EllarSQLModule",
    "EllarSQLService",
    "SQLAlchemyConfig",
    "MigrationOption",
    "get_or_404_async",
    "get_or_404",
    "first_or_404_async",
    "first_or_404",
    "one_or_404_async",
    "one_or_404",
    "paginate",
    "PageNumberPagination",
    "LimitOffsetPagination",
]
