import typing as t

import sqlalchemy as sa
import sqlalchemy.event as sa_event
import sqlalchemy.orm as sa_orm

from .base import Model
from .table import Table
from .typeDecorator import GUID, GenericIP
from .utils import make_metadata

if t.TYPE_CHECKING:
    from sqlalchemy import *  # type:ignore[assignment]
    from sqlalchemy.event import *  # noqa
    from sqlalchemy.orm import *  # noqa

    from .table import Table

__all__ = ["Model", "Table", "make_metadata", "GUID", "GenericIP"]


def __getattr__(name: str) -> t.Any:
    if name == "event":
        return sa_event

    if name.startswith("_"):
        raise AttributeError(name)

    for mod in (sa, sa_orm):
        if hasattr(mod, name):
            return getattr(mod, name)

    raise AttributeError(name)
