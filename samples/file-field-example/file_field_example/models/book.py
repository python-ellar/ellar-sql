from ellar_sql import model


class Book(model.Model):
    __tablename__ = "books"

    id: model.Mapped[int] = model.mapped_column(autoincrement=True, primary_key=True)
    title: model.Mapped[str] = model.mapped_column(model.String(100), unique=True)

    cover: model.Mapped[model.typeDecorator.File] = model.mapped_column(
        model.typeDecorator.ImageField(
            thumbnail_size=(128, 128), upload_storage="bookstore"
        )
    )
