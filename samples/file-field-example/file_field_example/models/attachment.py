from ellar_sql import model


class Attachment(model.Model):
    __tablename__ = "attachments"

    id: model.Mapped[int] = model.mapped_column(autoincrement=True, primary_key=True)
    name: model.Mapped[str] = model.mapped_column(model.String(50), unique=True)
    content: model.Mapped[model.typeDecorator.File] = model.mapped_column(
        model.typeDecorator.FileField
    )
