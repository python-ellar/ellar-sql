import os

from ellar_sql import model


class Base(model.Model):
    __base_config__ = {"make_declarative_base": True}


class User(Base):
    id = model.Column(model.Integer, primary_key=True)

    if os.environ.get("model_change_name"):
        name = model.Column(model.String(128))
    else:
        name = model.Column(model.String(256))


if os.environ.get("multiple_db"):

    class Group(Base):
        __database__ = "db1"
        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(128))
