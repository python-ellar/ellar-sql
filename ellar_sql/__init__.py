"""EllarSQL Module adds support for SQLAlchemy and Alembic package to your Ellar application"""

__version__ = "0.0.6"

from .model.database_binds import get_all_metadata, get_metadata
from .module import EllarSQLModule
from .pagination import LimitOffsetPagination, PageNumberPagination, paginate
from .query import first_or_404, first_or_none, get_or_404, get_or_none, one_or_404
from .schemas import MigrationOption, ModelBaseConfig, SQLAlchemyConfig
from .services import EllarSQLService

__all__ = [
    "EllarSQLModule",
    "EllarSQLService",
    "SQLAlchemyConfig",
    "MigrationOption",
    "get_or_404",
    "first_or_404",
    "one_or_404",
    "first_or_none",
    "get_or_none",
    "paginate",
    "PageNumberPagination",
    "LimitOffsetPagination",
    "ModelBaseConfig",
    "get_metadata",
    "get_all_metadata",
]
