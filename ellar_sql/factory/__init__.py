try:
    import factory
except ImportError as im_ex:  # pragma: no cover
    raise RuntimeError(
        "factory-boy not found. Please run `pip install factory-boy`"
    ) from im_ex

from factory.alchemy import SESSION_PERSISTENCE_COMMIT, SESSION_PERSISTENCE_FLUSH

from .base import EllarSQLFactory

__all__ = [
    "EllarSQLFactory",
    "SESSION_PERSISTENCE_COMMIT",
    "SESSION_PERSISTENCE_FLUSH",
]
