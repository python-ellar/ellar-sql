from ellar_sql import model


def test_model_include(db_service, ignore_base):
    class User(model.Model):
        id: model.Mapped[int] = model.Column(model.Integer, primary_key=True)
        name: model.Mapped[str] = model.Column(model.String)
        email: model.Mapped[str] = model.Column(model.String)

    db_service.create_all()
    session = db_service.session_factory()

    user = User(name="First User")

    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.dict() == {"id": 1, "name": "First User"}

    session.close()
