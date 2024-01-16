from ellar_sqlalchemy import EllarSQLAlchemyService, model
from ellar_sqlalchemy.schemas import ModelBaseConfig


async def test_scope(anyio_backend, ignore_base, app_setup) -> None:
    app = app_setup()
    async with app.application_context():
        first = app.injector.get(model.Session)
        second = app.injector.get(model.Session)
        assert first is second
        assert isinstance(first, model.Session)

    async with app.application_context():
        third = app.injector.get(model.Session)
        assert first is not third


async def test_custom_scope(ignore_base, app_setup, anyio_backend):
    count = 0

    def scope() -> int:
        nonlocal count
        count += 1
        return count

    app = app_setup(sql_module={"session_options": {"scopefunc": scope}})

    async with app.application_context():
        first = app.injector.get(model.Session)
        second = app.injector.get(model.Session)
        assert first is not second  # a new scope is generated on each call
        first.close()
        second.close()


def test_session_class(app_setup, ignore_base):
    class CustomSession(model.Session):
        pass

    app = app_setup(sql_module={"session_options": {"class_": CustomSession}})
    session = app.injector.get(model.Session)

    assert isinstance(session, CustomSession)
    session.close()


def test_session_uses_bind_key(app_setup, base_super_class, ignore_base):
    bases, _ = base_super_class

    class User(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases)
        id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)

    class Post(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases)
        __database__ = "a"
        id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)

    app = app_setup(
        sql_module={"databases": {"a": "sqlite://", "default": "sqlite://"}}
    )
    session = app.injector.get(model.Session)
    db_service = app.injector.get(EllarSQLAlchemyService)

    assert session.get_bind(mapper=User) is db_service.engine
    assert session.get_bind(mapper=Post) is db_service.engines["a"]

    session.close()


def test_session_uses_bind_key_map_as_dataclass(
    app_setup, base_super_class_as_dataclass, ignore_base
):
    bases, _ = base_super_class_as_dataclass

    class User(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases)
        id = model.Column(model.Integer, primary_key=True)

    class Post(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases)
        __database__ = "a"
        id = model.Column(model.Integer, primary_key=True)

    app = app_setup(
        sql_module={"databases": {"a": "sqlite://", "default": "sqlite://"}}
    )
    session = app.injector.get(model.Session)
    db_service = app.injector.get(EllarSQLAlchemyService)

    assert session.get_bind(mapper=User) is db_service.engine
    assert session.get_bind(mapper=Post) is db_service.engines["a"]

    session.close()


def test_get_bind_inheritance(base_super_class_as_dataclass, app_setup, ignore_base):
    bases, _ = base_super_class_as_dataclass

    class User(model.Model):
        __database__ = "a"
        __base_config__ = ModelBaseConfig(use_bases=bases)
        id: model.Mapped[int] = model.mapped_column(
            model.Integer, primary_key=True, init=False
        )
        type: model.Mapped[str] = model.mapped_column(
            model.String, nullable=False, init=False
        )
        __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "user"}

    class Admin(User):
        id: model.Mapped[int] = model.mapped_column(
            model.ForeignKey(User.id), primary_key=True, init=False
        )
        org: model.Mapped[str] = model.mapped_column(model.String, nullable=False)
        __mapper_args__ = {"polymorphic_identity": "admin"}

    app = app_setup(
        sql_module={"databases": {"a": "sqlite://", "default": "sqlite://"}}
    )
    db_service = app.injector.get(EllarSQLAlchemyService)
    db_service.create_all()

    session = db_service.session_factory()
    session.add(Admin(org="pallets"))
    session.commit()

    admin = session.execute(model.select(Admin)).scalar_one()
    session.expire(admin)
    assert admin.org == "pallets"


def test_get_bind_inheritance_case_2(app_setup, base_super_class, ignore_base):
    bases, _ = base_super_class

    class User(model.Model):
        __database__ = "a"
        id = model.Column(model.Integer, primary_key=True)
        type = model.Column(model.String, nullable=False)
        __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "user"}

    class Admin(User):
        id = model.Column(model.ForeignKey(User.id), primary_key=True)
        org = model.Column(model.String, nullable=False)
        __mapper_args__ = {"polymorphic_identity": "admin"}

    app = app_setup(
        sql_module={"databases": {"a": "sqlite://", "default": "sqlite://"}}
    )
    db_service = app.injector.get(EllarSQLAlchemyService)
    db_service.create_all()

    session = db_service.session_factory()
    session.add(Admin(org="pallets"))
    session.commit()

    admin = session.execute(model.select(Admin)).scalar_one()
    session.expire(admin)
    assert admin.org == "pallets"


def test_session_multiple_dbs_case_1(
    app_setup, ignore_base, base_super_class_as_dataclass
):
    bases, _ = base_super_class_as_dataclass

    class Base(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases, make_declarative_base=True)

    class User(Base):
        id: model.Mapped[int] = model.mapped_column(
            model.Integer, primary_key=True, init=False
        )
        name: model.Mapped[str] = model.mapped_column(
            model.String(50), nullable=False, init=False
        )

    class Product(Base):
        __database__ = "db1"
        id: model.Mapped[int] = model.mapped_column(
            model.Integer, primary_key=True, init=False
        )
        name: model.Mapped[str] = model.mapped_column(
            model.String(50), nullable=False, init=False
        )

    app = app_setup(
        sql_module={"databases": {"db1": "sqlite:///", "default": "sqlite://"}}
    )
    db_service = app.injector.get(EllarSQLAlchemyService)
    db_service.create_all()

    session = db_service.session_factory()

    session.execute(User.__table__.insert(), [{"name": "User1"}, {"name": "User2"}])
    session.commit()
    users = session.execute(model.select(User)).scalars().all()
    assert len(users) == 2

    session.execute(
        Product.__table__.insert(), [{"name": "Product1"}, {"name": "Product2"}]
    )
    session.commit()
    products = session.execute(model.select(Product)).scalars().all()
    assert len(products) == 2


def test_session_multiple_dbs(app_setup, ignore_base, base_super_class):
    bases, _ = base_super_class

    class User(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases)

        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(50), nullable=False)

    class Product(model.Model):
        __base_config__ = ModelBaseConfig(use_bases=bases)

        __database__ = "db1"

        id = model.Column(model.Integer, primary_key=True)
        name = model.Column(model.String(50), nullable=False)

    app = app_setup(
        sql_module={"databases": {"db1": "sqlite:///", "default": "sqlite://"}}
    )
    db_service = app.injector.get(EllarSQLAlchemyService)
    db_service.create_all()

    session = db_service.session_factory()

    session.execute(User.__table__.insert(), [{"name": "User1"}, {"name": "User2"}])
    session.commit()
    users = session.execute(model.select(User)).scalars().all()
    assert len(users) == 2

    session.execute(
        Product.__table__.insert(), [{"name": "Product1"}, {"name": "Product2"}]
    )
    session.commit()
    products = session.execute(model.select(Product)).scalars().all()
    assert len(products) == 2
