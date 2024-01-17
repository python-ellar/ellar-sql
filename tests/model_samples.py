from ellar_sql import model
from ellar_sql.schemas import ModelBaseConfig


class Base(model.Model):
    __base_config__ = ModelBaseConfig(make_declarative_base=True)

    metadata = model.MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class UserMixin(model.Model):
    __abstract__ = True
    name = model.Column(model.String(128))


class User(UserMixin):
    id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
    name = model.Column(model.String(128))


assert User.__tablename__ == "user"
