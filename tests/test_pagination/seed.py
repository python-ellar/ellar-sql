import typing as t

from ellar.app import App
from ellar.threading import execute_coroutine_with_sync_worker

from ellar_sql import EllarSQLService, model


def create_model():
    class User(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)

    return User


def seed_100_users(app: App):
    user_model = create_model()
    db_service = app.injector.get(EllarSQLService)

    session = db_service.session_factory()

    if session.get_bind().dialect.is_async:
        execute_coroutine_with_sync_worker(db_service.create_all_async())
    else:
        db_service.create_all()

    for i in range(100):
        session.add(user_model(name=f"User Number {i+1}"))

    res = session.commit()
    if isinstance(res, t.Coroutine):
        execute_coroutine_with_sync_worker(res)

    return user_model
