import factory
from db_learning.models import User
from ellar.app import current_injector
from sqlalchemy.orm import Session

from ellar_sql.factory import SESSION_PERSISTENCE_FLUSH, EllarSQLFactory


def _get_session():
    session = current_injector.get(Session)
    return session


class UserFactory(EllarSQLFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = SESSION_PERSISTENCE_FLUSH
        sqlalchemy_session_factory = _get_session

    username = factory.Faker("user_name")
    email = factory.Faker("email")
