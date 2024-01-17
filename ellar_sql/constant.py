import sqlalchemy.orm as sa_orm

DATABASE_BIND_KEY = "database_bind_key"
DEFAULT_KEY = "default"
DATABASE_KEY = "__database__"
TABLE_KEY = "__table__"
ABSTRACT_KEY = "__abstract__"
PAGINATION_OPTIONS = "__PAGINATION_OPTIONS__"
NAMING_CONVERSION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class DeclarativeBasePlaceHolder(sa_orm.DeclarativeBase):
    pass
