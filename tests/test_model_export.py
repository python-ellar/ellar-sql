import factory
import pytest
from factory.alchemy import SESSION_PERSISTENCE_COMMIT

from ellar_sql import model
from ellar_sql.factory.base import EllarSQLFactory


def get_model_factory(db_service):
    class User(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)
        email: model.Mapped[str] = model.Column(model.String)
        address: model.Mapped[str] = model.Column(model.String, nullable=True)
        city: model.Mapped[str] = model.Column(model.String, nullable=True)

    class UserFactory(EllarSQLFactory):
        class Meta:
            model = User
            sqlalchemy_session_factory = db_service.session_factory
            sqlalchemy_session_persistence = SESSION_PERSISTENCE_COMMIT

        name = factory.Faker("name")
        email = factory.Faker("email")
        city = factory.Faker("city")

    return UserFactory


class TestModelExport:
    def test_model_export_without_filter(self, db_service, ignore_base):
        user_factory = get_model_factory(db_service)

        db_service.create_all()

        user = user_factory(
            name="Ellar", email="ellar@support.com", city="Andersonchester"
        )
        assert user.dict() == {
            "address": None,
            "city": "Andersonchester",
            "email": "ellar@support.com",
            "id": 1,
            "name": "Ellar",
        }
        # db_service.session_factory.close()

    def test_model_exclude_none(self, db_service, ignore_base):
        user_factory = get_model_factory(db_service)

        db_service.create_all()

        user = user_factory(
            name="Ellar", email="ellar@support.com", city="Andersonchester"
        )
        assert user.dict(exclude_none=True) == {
            "city": "Andersonchester",
            "email": "ellar@support.com",
            "id": 1,
            "name": "Ellar",
        }
        # db_service.session_factory.close()

    def test_model_export_include(self, db_service, ignore_base):
        user_factory = get_model_factory(db_service)

        db_service.create_all()

        user = user_factory()

        assert user.dict(include={"email", "id", "name"}).keys() == {
            "email",
            "id",
            "name",
        }
        # db_service.session_factory.close()

    def test_model_export_exclude(self, db_service, ignore_base):
        user_factory = get_model_factory(db_service)

        db_service.create_all()

        user = user_factory()

        assert user.dict(exclude={"email", "name"}).keys() == {"address", "city", "id"}
        # db_service.session_factory.close()


@pytest.mark.asyncio
class TestModelExportAsync:
    async def test_model_export_without_filter_async(
        self, db_service_async, ignore_base
    ):
        user_factory = get_model_factory(db_service_async)

        db_service_async.create_all()

        user = user_factory(
            name="Ellar", email="ellar@support.com", city="Andersonchester"
        )
        assert user.dict() == {
            "address": None,
            "city": "Andersonchester",
            "email": "ellar@support.com",
            "id": 1,
            "name": "Ellar",
        }

    async def test_model_exclude_none_async(self, db_service_async, ignore_base):
        user_factory = get_model_factory(db_service_async)

        db_service_async.create_all()

        user = user_factory(
            name="Ellar", email="ellar@support.com", city="Andersonchester"
        )
        assert user.dict(exclude_none=True) == {
            "city": "Andersonchester",
            "email": "ellar@support.com",
            "id": 1,
            "name": "Ellar",
        }

    async def test_model_export_include_async(self, db_service_async, ignore_base):
        user_factory = get_model_factory(db_service_async)

        db_service_async.create_all()

        user = user_factory()

        assert user.dict(include={"email", "id", "name"}).keys() == {
            "email",
            "id",
            "name",
        }

    async def test_model_export_exclude_async(self, db_service_async, ignore_base):
        user_factory = get_model_factory(db_service_async)

        db_service_async.create_all()

        user = user_factory()

        assert user.dict(exclude={"email", "name"}).keys() == {"address", "city", "id"}
