from ellar_sql import EllarSQLService, model


class User(model.Model):
    id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)
    username: model.Mapped[str] = model.mapped_column(
        model.String, unique=True, nullable=False
    )
    email: model.Mapped[str] = model.mapped_column(model.String)


def main():
    db_service = EllarSQLService(
        databases="sqlite:///app.db",
        echo=True,
    )

    db_service.create_all()

    session = db_service.session_factory()

    for i in range(50):
        session.add(
            User(username=f"username-{i + 1}", email=f"user{i + 1}doe@example.com")
        )

    session.commit()
    rows = session.execute(model.select(User)).scalars()

    all_users = [row.dict() for row in rows]
    assert len(all_users) == 50

    session.close()


if __name__ == "__main__":
    main()
