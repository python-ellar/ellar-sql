import ipaddress
import typing as t

import sqlalchemy as sa
import sqlalchemy.dialects as sa_dialects


class GenericIP(sa.TypeDecorator):  # type:ignore[type-arg]
    """
    Platform-independent IP Address type.

    Uses PostgreSQL's INET type, otherwise uses
    CHAR(45), storing as stringified values.
    """

    impl = sa.CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: sa.Dialect) -> t.Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(sa_dialects.postgresql.INET())  # type:ignore[attr-defined]
        else:
            return dialect.type_descriptor(sa.CHAR(45))

    def process_bind_param(
        self, value: t.Optional[t.Any], dialect: sa.Dialect
    ) -> t.Any:
        if value is not None:
            return str(value)

    def process_result_value(
        self, value: t.Optional[t.Any], dialect: sa.Dialect
    ) -> t.Any:
        if value is None:
            return value

        if not isinstance(value, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            value = ipaddress.ip_address(value)
        return value
