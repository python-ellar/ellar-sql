import types
import typing

import factory
import pytest
from factory import FactoryError
from factory.alchemy import SESSION_PERSISTENCE_COMMIT, SESSION_PERSISTENCE_FLUSH
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship

from ellar_sql import model
from ellar_sql.factory.base import EllarSQLFactory


def create_group_model(**kwargs):
    class User(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)
        email: model.Mapped[str] = model.Column(model.String)
        address: model.Mapped[str] = model.Column(model.String, nullable=True)
        city: model.Mapped[str] = model.Column(model.String, nullable=True)
        groups: model.Mapped[typing.List["Group"]] = relationship(
            "Group", back_populates="user"
        )

    class Group(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)
        user_id: model.Mapped[int] = model.Column(
            model.ForeignKey("user.id"), unique=True
        )

        user: model.Mapped[User] = relationship(
            "User", back_populates="groups", uselist=False
        )

    user_config = kwargs.pop("user", {})
    user_meta = types.new_class(
        "UserMeta", (), {}, lambda ns: ns.update(model=User, **user_config)
    )

    class UserFactory(EllarSQLFactory):
        class Meta(user_meta):
            pass

        name = factory.Faker("name")
        email = factory.Faker("email")
        city = factory.Faker("city")

    group_config = kwargs.pop("group", {})
    group_meta = types.new_class(
        "GroupMeta", (), {}, lambda ns: ns.update(model=Group, **group_config)
    )

    class GroupFactory(EllarSQLFactory):
        class Meta(group_meta):
            pass

        name = factory.Faker("name")
        user = factory.SubFactory(UserFactory)

    return GroupFactory


class TestModelFactory:
    def test_model_factory(self, db_service, ignore_base):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_COMMIT,
            },
            group={
                "sqlalchemy_session_factory": db_service.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_COMMIT,
            },
        )

        db_service.create_all()

        group = group_factory()
        assert group.dict().keys() == {"name", "user_id", "id"}
        db_service.session_factory.close()

    def test_model_factory_session_none(self, db_service, ignore_base):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service.session_factory,
            },
            group={
                "sqlalchemy_session_factory": db_service.session_factory,
            },
        )

        db_service.create_all()

        group = group_factory()
        assert f"<Group (pending {id(group)})>" == repr(group)
        assert group.dict().keys() != {"name", "user_id", "id"}
        db_service.session_factory.close()

    def test_model_factory_session_flush(self, db_service, ignore_base):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
            },
            group={
                "sqlalchemy_session_factory": db_service.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
            },
        )

        db_service.create_all()

        group = group_factory()
        assert group.dict().keys() == {"name", "user_id", "id"}
        db_service.session_factory.close()

    def test_model_factory_get_or_create(self, db_service, ignore_base):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_COMMIT,
            },
            group={
                "sqlalchemy_session_factory": db_service.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_COMMIT,
                "sqlalchemy_get_or_create": ("name",),
            },
        )
        db_service.create_all()

        group = group_factory()

        group2 = group_factory(name=group.name)

        group3 = group_factory(name="new group")

        assert group.user_id == group2.user_id != group3.user_id
        assert group.id == group2.id

        assert group.dict() == group2.dict() != group3.dict()

        db_service.session_factory.close()

    def test_model_factory_get_or_create_for_integrity_error(
        self, db_service, ignore_base
    ):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_COMMIT,
            },
            group={
                "sqlalchemy_session_factory": db_service.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_COMMIT,
                "sqlalchemy_get_or_create": ("name",),
            },
        )
        db_service.create_all()

        group = group_factory()

        with pytest.raises(IntegrityError):
            group_factory(name="new group", user=group.user)

        db_service.session_factory.close()


@pytest.mark.asyncio
class TestModelFactoryAsync:
    async def test_model_factory_async(self, db_service_async, ignore_base):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_COMMIT,
            },
            group={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_COMMIT,
            },
        )

        db_service_async.create_all()

        group = group_factory()
        assert group.dict().keys() == {"name", "user_id", "id"}
        await db_service_async.session_factory.close()

    async def test_model_factory_session_none_async(
        self, db_service_async, ignore_base
    ):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service_async.session_factory,
            },
            group={
                "sqlalchemy_session_factory": db_service_async.session_factory,
            },
        )

        db_service_async.create_all()

        group = group_factory()
        assert f"<Group (pending {id(group)})>" == repr(group)
        assert group.dict().keys() != {"name", "user_id", "id"}
        await db_service_async.session_factory.close()

    async def test_model_factory_session_flush_async(
        self, db_service_async, ignore_base
    ):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
            },
            group={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
            },
        )

        db_service_async.create_all()

        group = group_factory()
        assert group.dict().keys() == {"name", "user_id", "id"}
        await db_service_async.session_factory.close()

    async def test_model_factory_get_or_create_async(
        self, db_service_async, ignore_base
    ):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
            },
            group={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
                "sqlalchemy_get_or_create": ("name",),
            },
        )
        db_service_async.create_all()

        group = group_factory()

        group2 = group_factory(name=group.name)

        group3 = group_factory(name="new group")

        assert group.user_id == group2.user_id != group3.user_id
        assert group.id == group2.id

        assert group.dict() == group2.dict() != group3.dict()

        await db_service_async.session_factory.close()

    async def test_model_factory_get_or_create_for_integrity_error_async(
        self, db_service_async, ignore_base
    ):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
            },
            group={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
                "sqlalchemy_get_or_create": ("name",),
            },
        )
        db_service_async.create_all()

        group = group_factory()

        with pytest.raises(IntegrityError):
            group_factory(name="new group", user=group.user)

        await db_service_async.session_factory.close()

    async def test_model_factory_get_or_create_raises_error_for_missing_field_async(
        self, db_service_async, ignore_base
    ):
        group_factory = create_group_model(
            user={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
            },
            group={
                "sqlalchemy_session_factory": db_service_async.session_factory,
                "sqlalchemy_session_persistence": SESSION_PERSISTENCE_FLUSH,
                "sqlalchemy_get_or_create": ("name", "user_id"),
            },
        )
        db_service_async.create_all()
        with pytest.raises(FactoryError):
            group_factory()

        await db_service_async.session_factory.close()
