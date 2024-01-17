import uuid

from ellar_sql import model


def test_guid_column_type(db_service, ignore_base):
    uid = uuid.uuid4()

    class Guid(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id",
            model.GUID(),
            nullable=False,
            unique=True,
            primary_key=True,
            default=uuid.uuid4,
        )

    db_service.create_all()
    session = db_service.session_factory()
    session.add(Guid(id=uid))
    session.commit()

    guid = session.execute(model.select(Guid)).scalar()
    assert guid.id == uid
