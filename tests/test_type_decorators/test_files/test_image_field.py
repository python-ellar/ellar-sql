import base64
import tempfile
from contextlib import asynccontextmanager

import pytest

from ellar_sql import EllarSQLService, model
from ellar_sql.model.typeDecorator import ImageField
from ellar_sql.model.typeDecorator.file.exceptions import (
    ContentTypeValidationError,
    InvalidImageError,
)


@pytest.fixture
def fake_text_file():
    file = tempfile.NamedTemporaryFile(suffix=".txt")
    file.write(b"Trying to save text file as image")
    file.seek(0)
    return file


@pytest.fixture
def fake_invalid_image():
    file = tempfile.NamedTemporaryFile(suffix=".png")
    file.write(b"Pass through content type validation")
    file.seek(0)
    return file


@pytest.fixture
def fake_valid_image_content():
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAAHNJREFUKFOdkLEKwCAMRM/JwUFwdPb"
        "/v8RPEDcdBQcHJyUt0hQ6hGY6Li8XEhVjXM45aK3xVXNOtNagcs6LRAgB1toX23tHSgkUpEopyxhzGRw"
        "+EHljjBv03oM3KJYP1lofkJoHJs3T/4Gi1aJjxO+RPnwDur2EF1gNZukAAAAASUVORK5CYII="
    )


@pytest.fixture
def fake_valid_image(fake_valid_image_content):
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = fake_valid_image_content
    file.write(data)
    file.seek(0)
    return file


class Book(model.Model):
    id = model.Column(model.Integer, autoincrement=True, primary_key=True)
    title = model.Column(model.String(100), unique=True)
    cover = model.Column(ImageField)

    def __repr__(self):
        return f"<Book: id {self.id} ; name: {self.title}; cover {self.cover};>"  # pragma: no cover


@pytest.mark.asyncio
class TestImageField:
    @asynccontextmanager
    async def init_app(self, app_setup):
        app = app_setup()
        db_service = app.injector.get(EllarSQLService)

        db_service.create_all("default")
        session = db_service.session_factory()

        async with app.application_context():
            yield app, db_service, session

        db_service.drop_all("default")

    async def test_autovalidate_content_type(self, fake_text_file, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Book(title="Pointless Meetings", cover=fake_text_file))
            with pytest.raises(ContentTypeValidationError):
                session.flush()

    async def test_autovalidate_image(self, fake_invalid_image, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Book(title="Pointless Meetings", cover=fake_invalid_image))
            with pytest.raises(InvalidImageError):
                session.flush()

    async def test_create_image(
        self, fake_valid_image, fake_valid_image_content, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Book(title="Pointless Meetings", cover=fake_valid_image))
            session.flush()

            book = session.execute(
                model.select(Book).where(Book.title == "Pointless Meetings")
            ).scalar_one()
            assert book.cover.file.read() == fake_valid_image_content

            assert book.cover.width is not None
            assert book.cover.height is not None
