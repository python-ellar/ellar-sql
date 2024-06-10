from ellar_sql import model


class Article(model.Model):
    __tablename__ = "articles"

    id: model.Mapped[int] = model.mapped_column(autoincrement=True, primary_key=True)
    title: model.Mapped[str] = model.mapped_column(model.String(100), unique=True)

    documents: model.Mapped[dict] = model.mapped_column(
        model.typeDecorator.FileField(multiple=True, upload_storage="documents")
    )
