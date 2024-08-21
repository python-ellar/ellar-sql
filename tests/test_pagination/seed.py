import typing as t

from ellar.core import current_injector
from ellar.events import ensure_build_context

from ellar_sql import EllarSQLService, model


def create_model():
    class User(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)

    return User


def seed_100_users():
    user_model = create_model()

    @ensure_build_context(app_ready=True)
    async def _on_context():
        db_service = current_injector.get(EllarSQLService)

        session = db_service.session_factory()

        db_service.create_all()

        for i in range(100):
            session.add(user_model(name=f"User Number {i + 1}"))

        res = session.commit()
        if isinstance(res, t.Coroutine):
            await res

    _on_context()

    return user_model
