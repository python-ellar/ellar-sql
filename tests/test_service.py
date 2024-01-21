import pytest
import sqlalchemy.exc as sa_exc
from ellar.common.exceptions import ImproperConfiguration

from ellar_sql import model
from ellar_sql.constant import DATABASE_BIND_KEY, DEFAULT_KEY
from ellar_sql.model.database_binds import (
    __model_database_metadata__,
    get_metadata,
)
from ellar_sql.schemas import ModelBaseConfig
from ellar_sql.services import EllarSQLService


def test_service_default_setup_create_all(db_service, ignore_base):
    class User(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)

    db_service.create_all()
    session = db_service.session_factory()

    user = User(name="First User")

    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.dict() == {"id": 1, "name": "First User"}

    session.close()


def test_service_drop_all(db_service, ignore_base):
    class User(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)

    db_service.create_all()
    session = db_service.session_factory()

    user = User(name="First User")

    session.add(user)
    session.commit()

    db_service.drop_all()

    stmt = model.select(User).where(User.id == 1)
    with pytest.raises(Exception, match="no such table: user"):
        session.execute(stmt)


def test_custom_metadata_2x(ignore_base):
    custom_metadata = model.MetaData()

    class Base(model.Model):
        __base_config__ = ModelBaseConfig(
            use_bases=[model.DeclarativeBase], as_base=True
        )
        metadata = custom_metadata

    assert Base.metadata is custom_metadata
    assert Base.metadata.info[DATABASE_BIND_KEY] is DEFAULT_KEY


def test_metadata_per_bind(tmp_path, ignore_base):
    EllarSQLService(
        databases={
            "a": "sqlite:///app2.db",
            "default": "sqlite:///app.db",
        },
        root_path=str(tmp_path),
    )
    assert get_metadata("a").info[DATABASE_BIND_KEY] == "a"
    assert get_metadata("default").info[DATABASE_BIND_KEY] == "default"


def test_setup_fails_when_default_database_is_not_configured(tmp_path, ignore_base):
    with pytest.raises(ImproperConfiguration):
        EllarSQLService(
            databases={
                "a": "sqlite:///app2.db",
            },
            root_path=str(tmp_path),
        )

    with pytest.raises(ImproperConfiguration):
        EllarSQLService(
            databases={
                "a",
                "sqlite:///app2.db",
            },
            root_path=str(tmp_path),
        )


def test_copy_naming_convention(tmp_path, ignore_base):
    class Base(model.Model):
        __base_config__ = ModelBaseConfig(
            use_bases=[model.DeclarativeBase], as_base=True
        )
        metadata = model.MetaData(naming_convention={"pk": "spk_%(table_name)s"})

    EllarSQLService(
        databases={
            "a": "sqlite:///app2.db",
            "default": "sqlite:///app.db",
        },
        root_path=str(tmp_path),
    )
    assert Base.metadata.naming_convention["pk"] == "spk_%(table_name)s"
    assert (
        get_metadata("a").naming_convention == get_metadata("default").naming_convention
    )


#


def test_create_drop_all(tmp_path, ignore_base):
    db_service = EllarSQLService(
        databases={
            "a": "sqlite:///app2.db",
            "default": "sqlite:///app.db",
        },
        root_path=str(tmp_path),
    )

    class User(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    class Post(model.Model):
        __database__ = "a"
        id = model.Column(model.Integer, primary_key=True)

    session = db_service.session_factory()
    with pytest.raises(sa_exc.OperationalError):
        session.execute(model.select(User)).scalars()

    with pytest.raises(sa_exc.OperationalError):
        session.execute(model.select(Post)).scalars()

    db_service.create_all()
    session.execute(model.select(User)).scalars()
    session.execute(model.select(Post)).scalars()

    db_service.drop_all()

    with pytest.raises(sa_exc.OperationalError):
        session.execute(model.select(User)).scalars()

    with pytest.raises(sa_exc.OperationalError):
        session.execute(model.select(Post)).scalars()


@pytest.mark.parametrize("database_key", [["a"], ["a", "default"]])
def test_create_key_spec(database_key, tmp_path, ignore_base):
    db_service = EllarSQLService(
        databases={
            "a": "sqlite:///app2.db",
            "default": "sqlite:///app.db",
        },
        root_path=str(tmp_path),
    )

    class User(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    class Post(model.Model):
        __database__ = "a"
        id = model.Column(model.Integer, primary_key=True)

    db_service.create_all(*database_key)
    session = db_service.session_factory()
    session.execute(model.select(Post)).scalars()

    if "default" not in database_key:
        with pytest.raises(sa_exc.OperationalError):
            session.execute(model.select(User)).scalars()
    else:
        session.execute(model.select(User)).scalars()


def test_reflect(tmp_path, ignore_base):
    db_service = EllarSQLService(
        databases={
            "post": "sqlite:///post.db",
            "default": "sqlite:///user.db",
        },
        root_path=str(tmp_path),
    )
    model.Table("user", model.Column("id", model.Integer, primary_key=True))
    model.Table(
        "post", model.Column("id", model.Integer, primary_key=True), __database__="post"
    )
    db_service.create_all()
    del db_service
    __model_database_metadata__.clear()

    db_service = EllarSQLService(
        databases={
            "post": "sqlite:///post.db",
            "default": "sqlite:///user.db",
        },
        root_path=str(tmp_path),
    )
    default_metadata = get_metadata("default")
    assert not default_metadata.tables

    db_service.reflect()

    assert "user" in __model_database_metadata__["default"].tables
    assert "post" in __model_database_metadata__["post"].tables


@pytest.mark.asyncio
async def test_service_create_drop_all_async(tmp_path, ignore_base):
    db_service = EllarSQLService(
        databases={
            "a": "sqlite+aiosqlite:///app2.db",
            "default": "sqlite+aiosqlite:///app.db",
        },
        root_path=str(tmp_path),
    )

    class User(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    class Post(model.Model):
        __database__ = "a"
        id = model.Column(model.Integer, primary_key=True)

    session = db_service.session_factory()
    with pytest.raises(sa_exc.OperationalError):
        await session.execute(model.select(User))

    with pytest.raises(sa_exc.OperationalError):
        await session.execute(model.select(Post))

    db_service.create_all()

    user_res = await session.execute(model.select(User))
    user_res.scalars()
    post_res = await session.execute(model.select(Post))
    post_res.scalars()

    db_service.drop_all()

    with pytest.raises(sa_exc.OperationalError):
        await session.execute(model.select(User))

    with pytest.raises(sa_exc.OperationalError):
        await session.execute(model.select(Post))


@pytest.mark.asyncio
async def test_service_reflect_async(tmp_path, ignore_base):
    db_service = EllarSQLService(
        databases={
            "post": "sqlite+aiosqlite:///post.db",
            "default": "sqlite+aiosqlite:///user.db",
        },
        root_path=str(tmp_path),
    )
    model.Table("user", model.Column("id", model.Integer, primary_key=True))
    model.Table(
        "post", model.Column("id", model.Integer, primary_key=True), __database__="post"
    )
    db_service.create_all()
    del db_service
    __model_database_metadata__.clear()

    db_service = EllarSQLService(
        databases={
            "post": "sqlite+aiosqlite:///post.db",
            "default": "sqlite+aiosqlite:///user.db",
        },
        root_path=str(tmp_path),
    )
    default_metadata = get_metadata("default")
    assert not default_metadata.tables

    db_service.reflect()

    assert "user" in __model_database_metadata__["default"].tables
    assert "post" in __model_database_metadata__["post"].tables


@pytest.mark.asyncio
async def test_using_create_drop_reflect_async_for_sync_engine_work(
    db_service, ignore_base
):
    class User(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    db_service.create_all()
    session = db_service.session_factory()
    session.execute(model.select(User)).scalars()

    db_service.drop_all()

    with pytest.raises(sa_exc.OperationalError):
        session.execute(model.select(User)).scalars()

    db_service.reflect()
