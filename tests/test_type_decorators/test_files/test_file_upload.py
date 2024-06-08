import tempfile
from contextlib import asynccontextmanager

import pytest
from ellar.common.datastructures import ContentFile
from ellar_storage import StorageService
from libcloud.storage.types import ObjectDoesNotExistError

from ellar_sql import EllarSQLService, model


@pytest.fixture
def fake_content():
    return "This is a fake file"


@pytest.fixture
def fake_file(fake_content):
    file = tempfile.NamedTemporaryFile(suffix=".txt")
    file.write(fake_content.encode())
    file.seek(0)
    return file


class Attachment(model.Model):
    id = model.Column(model.Integer, autoincrement=True, primary_key=True)
    name = model.Column(model.String(50), unique=True)
    content = model.Column(model.typeDecorator.FileField)

    article_id = model.Column(model.Integer, model.ForeignKey("article.id"))

    def __repr__(self):
        return "<Attachment: id {} ; name: {}; content {}; article_id {}>".format(
            self.id,
            self.name,
            self.content,
            self.article_id,
        )  # pragma: no cover


class Article(model.Model):
    id = model.Column(model.Integer, autoincrement=True, primary_key=True)
    title = model.Column(model.String(100), unique=True)

    attachments = model.relationship(Attachment, cascade="all, delete-orphan")

    def __repr__(self):
        return "<Article id: %s; name: %s; attachments: (%d) %s>" % (
            self.id,
            self.title,
            len(self.attachments),
            self.attachments,
        )  # pragma: no cover


@pytest.mark.asyncio
class TestSingleField:
    @asynccontextmanager
    async def init_app(self, app_setup):
        app = app_setup()
        db_service = app.injector.get(EllarSQLService)

        db_service.create_all("default")
        session = db_service.session_factory()

        async with app.application_context():
            yield app, db_service, session

        db_service.drop_all("default")

    async def test_create_from_string(self, fake_content, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Attachment(name="Create fake string", content=fake_content))
            session.commit()
            attachment = session.execute(
                model.select(Attachment).where(Attachment.name == "Create fake string")
            ).scalar_one()
            assert attachment.content.saved
            assert attachment.content.file.read() == fake_content.encode()

    async def test_create_from_bytes(self, fake_content, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                Attachment(name="Create Fake bytes", content=fake_content.encode())
            )
            session.commit()
            attachment = session.execute(
                model.select(Attachment).where(Attachment.name == "Create Fake bytes")
            ).scalar_one()
            assert attachment.content.saved
            assert attachment.content.file.read() == fake_content.encode()

    async def test_create_fromfile(self, fake_file, fake_content, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Attachment(name="Create Fake file", content=fake_file))
            session.commit()
            attachment = session.execute(
                model.select(Attachment).where(Attachment.name == "Create Fake file")
            ).scalar_one()
            assert attachment.content.saved
            assert attachment.content.file.read() == fake_content.encode()

    async def test_create_frompath(self, fake_file, fake_content, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                Attachment(
                    name="Create Fake file",
                    content=model.typeDecorator.File(content_path=fake_file.name),
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(Attachment).where(Attachment.name == "Create Fake file")
            ).scalar_one()
            assert attachment.content.saved
            assert attachment.content.file.read() == fake_content.encode()

    async def test_file_is_created_when_flush(
        self, fake_file, fake_content, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            attachment = Attachment(
                name="Create Fake file 2", content=model.typeDecorator.File(fake_file)
            )
            session.add(attachment)
            with pytest.raises(RuntimeError):
                assert attachment.content.file is not None
            session.flush()
            assert attachment.content.file is not None

    async def test_create_rollback(self, fake_file, fake_content, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Attachment(name="Create rollback", content=fake_file))
            session.flush()
            attachment = session.execute(
                model.select(Attachment).where(Attachment.name == "Create rollback")
            ).scalar_one()
            file_id = attachment.content.file_id

            storage_service: StorageService = app.injector.get(StorageService)

            assert storage_service.get_container().get_object(file_id) is not None
            session.rollback()
            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get_container().get_object(file_id)

    async def test_create_rollback_with_uploadFile(
        self, fake_file, fake_content, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                Attachment(
                    name="Create rollback",
                    content=ContentFile(b"UploadFile should work just fine"),
                )
            )
            session.flush()
            attachment = session.execute(
                model.select(Attachment).where(Attachment.name == "Create rollback")
            ).scalar_one()
            file_id = attachment.content.file_id

            storage_service: StorageService = app.injector.get(StorageService)

            assert storage_service.get_container().get_object(file_id) is not None
            session.rollback()
            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get_container().get_object(file_id)

    async def test_edit_existing(self, fake_file, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Attachment(name="Editing test", content=fake_file))
            session.commit()
            attachment = session.execute(
                model.select(Attachment).where(Attachment.name == "Editing test")
            ).scalar_one()
            old_file_id = attachment.content.file_id
            attachment.content = b"New content"
            session.add(attachment)
            session.commit()
            session.refresh(attachment)

            storage_service: StorageService = app.injector.get(StorageService)

            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get_container().get_object(old_file_id)
            assert attachment.content.file.read() == b"New content"

    async def test_edit_existing_none(self, fake_file, fake_content, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Attachment(name="Testing None edit", content=None))
            session.commit()
            attachment = session.execute(
                model.select(Attachment).where(Attachment.name == "Testing None edit")
            ).scalar_one()
            attachment.content = fake_file
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert attachment.content.file.read() == fake_content.encode()

    async def test_edit_existing_rollback(self, fake_file, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                Attachment(name="Editing test rollback", content=b"Initial content")
            )
            session.commit()
            attachment = session.execute(
                model.select(Attachment).where(
                    Attachment.name == "Editing test rollback"
                )
            ).scalar_one()
            old_file_id = attachment.content.file_id
            attachment.content = b"New content"
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            new_file_id = attachment.content.file_id
            session.rollback()

            storage_service: StorageService = app.injector.get(StorageService)

            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get_container().get_object(new_file_id)
            assert storage_service.get_container().get_object(old_file_id) is not None
            assert attachment.content.file.read() == b"Initial content"

    async def test_edit_existing_multiple_flush(self, fake_file, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            attachment = Attachment(
                name="Multiple flush edit", content=b"first content"
            )
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            before_first_edit_fileid = attachment.content.file_id
            attachment.content = b"first edit"
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            first_edit_fileid = attachment.content.file_id
            attachment.content = b"second edit"
            session.add(attachment)
            session.flush()
            second_edit_fileid = attachment.content.file_id
            session.commit()

            storage_service: StorageService = app.injector.get(StorageService)

            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get_container().get_object(before_first_edit_fileid)
            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get_container().get_object(first_edit_fileid)
            assert (
                storage_service.get_container().get_object(second_edit_fileid)
                is not None
            )
            assert attachment.content.file.read() == b"second edit"

    async def test_delete_existing(self, fake_file, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Attachment(name="Deleting test", content=fake_file))
            session.commit()
            attachment = session.execute(
                model.select(Attachment).where(Attachment.name == "Deleting test")
            ).scalar_one()
            file_id = attachment.content.file_id
            storage_service: StorageService = app.injector.get(StorageService)

            assert storage_service.get_container().get_object(file_id) is not None
            session.delete(attachment)
            session.commit()
            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get_container().get_object(file_id)

    async def test_delete_existing_rollback(self, fake_file, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(Attachment(name="Deleting rollback test", content=fake_file))
            session.commit()
            attachment = session.execute(
                model.select(Attachment).where(
                    Attachment.name == "Deleting rollback test"
                )
            ).scalar_one()
            file_id = attachment.content.file_id
            storage_service: StorageService = app.injector.get(StorageService)

            assert storage_service.get_container().get_object(file_id) is not None
            session.delete(attachment)
            session.flush()
            session.rollback()
            assert storage_service.get_container().get_object(file_id) is not None

    async def test_relationship(self, fake_file, fake_content, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            article = Article(title="Great article!")
            session.add(article)
            article.attachments.append(Attachment(name="Banner", content=fake_file))
            session.commit()
            article = session.execute(
                model.select(Article).where(Article.title == "Great article!")
            ).scalar_one()
            attachment = article.attachments[0]
            assert attachment.content.file.read() == fake_content.encode()
            file_path = attachment.content.path
            article.attachments.remove(attachment)
            session.add(article)
            session.commit()
            storage_service: StorageService = app.injector.get(StorageService)

            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get(file_path)

    async def test_relationship_rollback(
        self, fake_file, fake_content, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            article = Article(title="Awesome article about shark!")
            session.add(article)
            article.attachments.append(Attachment(name="Shark", content=fake_file))
            session.flush()
            article = session.execute(
                model.select(Article).where(
                    Article.title == "Awesome article about shark!"
                )
            ).scalar_one()
            attachment = article.attachments[0]
            assert attachment.content.file.read() == fake_content.encode()
            file_path = attachment.content.path
            session.rollback()
            storage_service: StorageService = app.injector.get(StorageService)

            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get(file_path)

    async def test_relationship_cascade_delete(
        self, fake_file, fake_content, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            article = Article(title="Another Great article!")
            session.add(article)
            article.attachments.append(
                Attachment(name="Another Banner", content=fake_file)
            )
            session.commit()
            article = session.execute(
                model.select(Article).where(Article.title == "Another Great article!")
            ).scalar_one()
            storage_service: StorageService = app.injector.get(StorageService)

            attachment = article.attachments[0]
            assert attachment.content.file.read() == fake_content.encode()
            file_path = attachment.content.path
            session.delete(article)
            session.commit()
            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get(file_path)

    async def test_relationship_cascade_delete_rollback(
        self, fake_file, fake_content, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            article = Article(title="Another Great article for rollback!")
            session.add(article)
            article.attachments.append(
                Attachment(name="Another Banner for rollback", content=fake_file)
            )
            session.commit()
            article = session.execute(
                model.select(Article).where(
                    Article.title == "Another Great article for rollback!"
                )
            ).scalar_one()
            file_path = article.attachments[0].content.path
            storage_service: StorageService = app.injector.get(StorageService)

            assert storage_service.get(file_path) is not None
            session.delete(article)
            session.flush()
            session.rollback()
            assert storage_service.get(file_path) is not None
