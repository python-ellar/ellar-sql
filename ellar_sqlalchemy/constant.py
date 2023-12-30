import sqlalchemy.orm as sa_orm

DATABASE_BIND_KEY = "database_bind_key"
DEFAULT_KEY = "default"
DATABASE_KEY = "__database__"
TABLE_KEY = "__table__"
ABSTRACT_KEY = "__abstract__"


class DeclarativeBasePlaceHolder(sa_orm.DeclarativeBase):
    pass
