from datetime import datetime
from sqlalchemy import DateTime, func, MetaData
from sqlalchemy.orm import Mapped, mapped_column

from ellar_sql.model import Model

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(Model):
  __base_config__ = {'as_base': True}
  __database__ = 'default'

  metadata = MetaData(naming_convention=convention)

  created_date: Mapped[datetime] = mapped_column(
      "created_date", DateTime, default=datetime.utcnow, nullable=False
  )

  time_updated: Mapped[datetime] = mapped_column(
      "time_updated", DateTime, nullable=False, default=datetime.utcnow, onupdate=func.now()
  )
