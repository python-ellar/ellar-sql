from ellar_sql import model
from ellar_sql.model.database_binds import get_database_bind


def test_bind_key_default(ignore_base):
    class User(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    assert User.metadata is get_database_bind("default", certain=True)


def test_metadata_per_bind(ignore_base):
    class User(model.Model):
        __database__ = "other"
        id = model.Column(model.Integer, primary_key=True)

    assert User.metadata is get_database_bind("other", certain=True)


def test_multiple_binds_same_table_name(ignore_base):
    class UserA(model.Model):
        __tablename__ = "user"
        id = model.Column(model.Integer, primary_key=True)

    class UserB(model.Model):
        __database__ = "other"
        __tablename__ = "user"
        id = model.Column(model.Integer, primary_key=True)

    assert UserA.metadata is get_database_bind("default", certain=True)
    assert UserB.metadata is get_database_bind("other", certain=True)
    assert UserA.__table__.metadata is not UserB.__table__.metadata


def test_inherit_parent(ignore_base):
    class User(model.Model):
        __database__ = "auth"
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        type = model.Column(model.String)
        __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "user"}

    class Admin(User):
        id = model.Column(model.Integer, model.ForeignKey(User.id), primary_key=True)
        __mapper_args__ = {"polymorphic_identity": "admin"}

    assert "admin" in get_database_bind("auth", certain=True).tables
    # inherits metadata, doesn't set it directly
    assert "metadata" not in Admin.__dict__


def test_inherit_abstract_parent(ignore_base):
    class AbstractUser(model.Model):
        __abstract__ = True
        __database__ = "auth"

    class User(AbstractUser):
        id = model.Column(model.Integer, primary_key=True)

    assert "user" in get_database_bind("auth", certain=True).tables
    assert "metadata" not in User.__dict__


def test_explicit_metadata(ignore_base) -> None:
    other_metadata = model.MetaData()

    class User(model.Model):
        __database__ = "other"
        metadata = other_metadata
        id = model.Column(model.Integer, primary_key=True)

    assert User.__table__.metadata is other_metadata
    assert get_database_bind("other") is None


def test_explicit_table(ignore_base):
    user_table = model.Table(
        "user",
        model.Column("id", model.Integer, primary_key=True),
        __database__="auth",
    )

    class User(model.Model):
        __database__ = "other"
        __table__ = user_table

    assert User.__table__.metadata is get_database_bind("auth")
    assert get_database_bind("other") is None
