import typing as t

from ellar.app import App
from ellar.threading import run_as_async

from ellar_sql import EllarSQLService, model


def create_model():
    class User(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)

    return User


@run_as_async
async def seed_100_users(app: App):
    user_model = create_model()
    db_service = app.injector.get(EllarSQLService)

    session = db_service.session_factory()

    db_service.create_all()

    for i in range(100):
        session.add(user_model(name=f"User Number {i+1}"))

    res = session.commit()
    if isinstance(res, t.Coroutine):
        await res

    return user_model
