from datetime import datetime

import pytest

from ellar_sql import model
from ellar_sql.model.mixins import get_registered_models
from ellar_sql.schemas import ModelBaseConfig

from .model_samples import Base


def test_model_creation():
    class T1(Base):
        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(128))

    class T2(Base):
        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(128))

    assert T1.metadata == T2.metadata
    assert T1.metadata.info["database_bind_key"] == "default"

    assert T1.__tablename__ == "t1"
    assert T2.__tablename__ == "t2"

    registered_models = get_registered_models()
    assert registered_models[str(T1)] == T1
    assert registered_models[str(T2)] == T2


def test_create_model_with_another_base():
    class AnotherBaseWithSameMetadata(model.Model):
        __base_config__ = ModelBaseConfig(as_base=True)
        name = model.Column(model.String(128))

    class T3(AnotherBaseWithSameMetadata):
        id = model.Column(model.Integer, primary_key=True)

    class T4(AnotherBaseWithSameMetadata):
        id = model.Column(model.Integer, primary_key=True)

    assert (
        T3.metadata
        == T4.metadata
        == Base.metadata
        == AnotherBaseWithSameMetadata.metadata
    )

    assert T3.name
    assert T4.name

    assert T4.metadata.info["database_bind_key"] == "default"

    assert T4.__tablename__ == "t4"
    assert T3.__tablename__ == "t3"
    assert not hasattr(Base, "__tablename__")


def test_metadata():
    class Base2(model.Model):
        __base_config__ = ModelBaseConfig(as_base=True)
        metadata = model.MetaData()
        __database__ = "db2"
        name = model.Column(model.String(128))

    assert Base2.metadata != Base.metadata

    class Base3(model.Model):
        __base_config__ = ModelBaseConfig(
            use_bases=[model.DeclarativeBase], as_base=True
        )
        __database__ = "db2"
        name = model.Column(model.String(128))

    assert Base3.metadata == Base2.metadata


def test_create_model_with_different_metadata():
    class T3(Base):
        __database__ = "db2"
        id = model.Column(model.Integer, primary_key=True)

    class T4(Base):
        __database__ = "db2"
        id = model.Column(model.Integer, primary_key=True)

    assert T3.metadata == T4.metadata != Base.metadata
    assert T4.metadata.info["database_bind_key"] == "db2"

    assert T4.__tablename__ == "t4"
    assert T3.__tablename__ == "t3"


def test_skips_name_generation_case_1():
    # when there is already a __tablename__ defined
    class WithoutNameDefined(Base):
        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(128))

    class WithNameDefined(Base):
        __tablename__ = "NameDefined"
        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(128))

    assert WithoutNameDefined.__tablename__ == "without_name_defined"
    assert WithNameDefined.__tablename__ == "NameDefined"


def test_skips_name_generation_case_2():
    # when there is already a __tablename__ defined as a declarative_attr
    class WithNameDefined(Base):
        @model.declared_attr
        def __tablename__(self):
            return "NameDefinedCase2"

        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(128))

    assert WithNameDefined.__tablename__ == "NameDefinedCase2"


def test_skips_name_generation_case_3():
    # when there is __abstract__ code defined.
    class WithNameDefined(Base):
        __abstract__ = True

        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(128))

    assert hasattr(WithNameDefined, "__tablename__") is False


def test_getting_db_session_fails_outside_app_context():
    class Ellar(Base):
        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(128))

    with pytest.raises(RuntimeError) as ex:
        Ellar.get_db_session()

    assert str(ex.value) == "ApplicationContext is not available at this scope."


def test_abstractmodel_case_1(db_service, base_super_class_as_dataclass):
    bases, _ = base_super_class_as_dataclass

    class Base(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases, as_base=True)

    class TimestampModel(Base):
        __abstract__ = True
        created: model.Mapped[datetime] = model.mapped_column(
            model.DateTime, nullable=False, insert_default=datetime.utcnow, init=False
        )
        updated: model.Mapped[datetime] = model.mapped_column(
            model.DateTime,
            insert_default=datetime.utcnow,
            onupdate=datetime.utcnow,
            init=False,
        )

    class Post(TimestampModel):
        id: model.Mapped[int] = model.mapped_column(
            model.Integer, primary_key=True, init=False
        )
        title: model.Mapped[str] = model.mapped_column(model.String, nullable=False)

    db_service.create_all()
    session = db_service.session_factory()
    session.add(Post(title="Admin Post"))

    session.commit()
    post = session.execute(model.select(Post)).scalar()
    assert post is not None
    assert post.created is not None
    assert post.updated is not None

    assert post.dict(exclude={"created", "updated"}) == {"id": 1, "title": "Admin Post"}


def test_abstractmodel_case_2(db_service, base_super_class):
    bases, meta = base_super_class

    # @model.as_base()
    class Base(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases, as_base=True)

    class TimestampModel(Base):  # type: ignore[no-redef]
        __abstract__ = True
        created = model.Column(model.DateTime, nullable=False, default=datetime.utcnow)
        updated = model.Column(
            model.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow
        )

    class Post(TimestampModel):  # type: ignore[no-redef]
        id = model.Column(model.Integer, primary_key=True)
        title = model.Column(model.String, nullable=False)

    db_service.create_all()
    session = db_service.session_factory()
    session.add(Post(title="Admin Post"))
    session.commit()
    post: Post = session.execute(model.select(Post)).scalar()
    assert post is not None
    assert post.created is not None
    assert post.updated is not None

    assert post.dict(exclude={"created", "updated"}) == {"id": 1, "title": "Admin Post"}


def test_mixin_model(db_service, ignore_base):
    class TimestampMixin:  # type: ignore[no-redef]
        created: model.Mapped[datetime] = model.mapped_column(
            model.DateTime, nullable=False, default=datetime.utcnow
        )
        updated: model.Mapped[datetime] = model.mapped_column(
            model.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        )

    class Post(TimestampMixin, model.Model):  # type: ignore[no-redef]
        id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)
        title: model.Mapped[str] = model.mapped_column(model.String, nullable=False)

    db_service.create_all()

    session = db_service.session_factory()
    session.add(Post(title="Admin Post"))

    session.commit()
    post = session.execute(model.select(Post)).scalar()

    assert post is not None
    assert post.created is not None
    assert post.updated is not None


def test_mixin_model_with_model_base(db_service, ignore_base):
    class TimestampMixin:  # type: ignore[no-redef]
        created: model.Mapped[datetime] = model.mapped_column(
            model.DateTime, nullable=False, default=datetime.utcnow
        )
        updated: model.Mapped[datetime] = model.mapped_column(
            model.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        )

    class Base(TimestampMixin, model.Model):
        __base_config__ = ModelBaseConfig(as_base=True)

    class Post(Base):  # type: ignore[no-redef]
        id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)
        title: model.Mapped[str] = model.mapped_column(model.String, nullable=False)

    db_service.create_all()

    session = db_service.session_factory()
    session.add(Post(title="Admin Post"))

    session.commit()
    post = session.execute(model.select(Post)).scalar()

    assert post is not None
    assert post.created is not None
    assert post.updated is not None


def test_mixin_model_case_2(db_service, base_super_class_as_dataclass) -> None:
    bases, meta = base_super_class_as_dataclass

    class Base(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases, as_base=True)

    class TimestampMixin(model.MappedAsDataclass):
        created: model.Mapped[datetime] = model.mapped_column(
            model.DateTime, nullable=False, insert_default=datetime.utcnow, init=False
        )
        updated: model.Mapped[datetime] = model.mapped_column(
            model.DateTime,
            insert_default=datetime.utcnow,
            onupdate=datetime.utcnow,
            init=False,
        )

    class Post(TimestampMixin, Base):
        id: model.Mapped[int] = model.mapped_column(
            model.Integer, primary_key=True, init=False
        )
        title: model.Mapped[str] = model.mapped_column(model.String, nullable=False)

    db_service.create_all()
    session = db_service.session_factory()
    session.add(Post(title="Admin Post"))

    session.commit()
    post = session.execute(model.select(Post)).scalar()
    # post.dict()
    assert post is not None
    assert post.created is not None
    assert post.updated is not None


def test_model_repr(db_service, ignore_base) -> None:
    class User(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    db_service.create_all()
    session = db_service.session_factory()

    user = User()
    assert repr(user) == f"<User (transient {id(user)})>"
    session.add(user)
    assert repr(user) == f"<User (pending {id(user)})>"
    session.flush()
    assert repr(user) == f"<User {user.id}>"


def test_model_repr_for_mapped_as_dataclass(db_service, ignore_base) -> None:
    class User(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=[model.MappedAsDataclass])

        id = model.Column(model.Integer, primary_key=True)

    user = User()
    assert repr(user) == "test_model_repr_for_mapped_as_dataclass.<locals>.User()"


def test_cant_inherit_any_declarative_base(ignore_base):
    with pytest.raises(TypeError, match="metaclass conflict:"):

        class _Base(model.Model, model.DeclarativeBase):  # type: ignore[misc]
            pass

    with pytest.raises(TypeError, match="metaclass conflict:"):

        class _Base(model.Model, model.MappedAsDataclass):  # type: ignore[misc]
            pass


def test_too_many_bases(ignore_base):
    with pytest.raises(
        ValueError, match="Only one declarative base can be passed to SQLAlchemy."
    ):

        class _Base(model.Model):  # type: ignore[misc]
            __base_config__ = ModelBaseConfig(
                use_bases=[model.DeclarativeBase, model.DeclarativeBaseNoMeta]
            )
