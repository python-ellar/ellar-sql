import tempfile
from contextlib import asynccontextmanager

import pytest
from ellar_storage import StorageService
from libcloud.storage.types import ObjectDoesNotExistError

from ellar_sql import EllarSQLService, model


@pytest.fixture
def fake_content():
    return "This is a fake file"


@pytest.fixture
def fake_file(fake_content):
    file = tempfile.NamedTemporaryFile()
    file.write(fake_content.encode())
    file.seek(0)
    return file


class AttachmentMultipleFields(model.Model):
    id = model.Column(model.Integer, autoincrement=True, primary_key=True)
    name = model.Column(model.String(50), unique=True)
    multiple_content = model.Column(model.typeDecorator.FileField(multiple=True))

    def __repr__(self):
        return "<Attachment: id {} ; name: {}; multiple_content {}>".format(
            self.id,
            self.name,
            self.multiple_content,
        )  # pragma: no cover


@pytest.mark.asyncio
class TestMultipleField:
    @asynccontextmanager
    async def init_app(self, app_setup):
        app = app_setup()
        db_service = app.injector.get(EllarSQLService)

        db_service.create_all("default")
        session = db_service.session_factory()

        async with app.application_context():
            yield app, db_service, session

        db_service.drop_all("default")

    async def test_create_multiple_content(
        self, fake_file, fake_content, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Create multiple",
                    multiple_content=[
                        "from str",
                        b"from bytes",
                        fake_file,
                    ],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name == "Create multiple"
                )
            ).scalar_one()
            assert attachment.multiple_content[0].file.read().decode() == "from str"
            assert attachment.multiple_content[1].file.read() == b"from bytes"
            assert attachment.multiple_content[2].file.read() == fake_content.encode()

    async def test_create_multiple_content_rollback(
        self, fake_file, fake_content, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Create multiple content rollback",
                    multiple_content=[
                        "from str",
                        b"from bytes",
                        fake_file,
                    ],
                )
            )
            session.flush()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name == "Create multiple content rollback"
                )
            ).scalar_one()
            paths = [p["path"] for p in attachment.multiple_content]
            storage_service: StorageService = app.injector.get(StorageService)
            assert all(storage_service.get(path) is not None for path in paths)
            session.rollback()

            for path in paths:
                with pytest.raises(ObjectDoesNotExistError):
                    storage_service.get(path)

    async def test_edit_existing_multiple_content(self, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Multiple content edit all",
                    multiple_content=[b"Content 1", b"Content 2"],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name == "Multiple content edit all"
                )
            ).scalar_one()
            old_paths = [f["path"] for f in attachment.multiple_content]
            attachment.multiple_content = [b"Content 1 edit", b"Content 2 edit"]
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert attachment.multiple_content[0].file.read() == b"Content 1 edit"
            assert attachment.multiple_content[1].file.read() == b"Content 2 edit"

            storage_service: StorageService = app.injector.get(StorageService)

            for path in old_paths:
                with pytest.raises(ObjectDoesNotExistError):
                    storage_service.get(path)

    async def test_edit_existing_multiple_content_rollback(self, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Multiple content edit all rollback",
                    multiple_content=[b"Content 1", b"Content 2"],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name
                    == "Multiple content edit all rollback"
                )
            ).scalar_one()
            old_paths = [f["path"] for f in attachment.multiple_content]
            attachment.multiple_content = [b"Content 1 edit", b"Content 2 edit"]
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert attachment.multiple_content[0].file.read() == b"Content 1 edit"
            assert attachment.multiple_content[1].file.read() == b"Content 2 edit"
            new_paths = [f["path"] for f in attachment.multiple_content]
            session.rollback()

            storage_service: StorageService = app.injector.get(StorageService)

            for path in new_paths:
                with pytest.raises(ObjectDoesNotExistError):
                    storage_service.get(path)
            for path in old_paths:
                assert storage_service.get(path) is not None

    async def test_edit_existing_multiple_content_add_element(self, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Multiple content add element",
                    multiple_content=[b"Content 1", b"Content 2"],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name == "Multiple content add element"
                )
            ).scalar_one()
            assert len(attachment.multiple_content) == 2
            attachment.multiple_content.append(b"Content 3")
            attachment.multiple_content += [b"Content 4"]
            attachment.multiple_content.extend([b"Content 5"])
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert len(attachment.multiple_content) == 5
            assert attachment.multiple_content[0].file.read() == b"Content 1"
            assert attachment.multiple_content[1].file.read() == b"Content 2"
            assert attachment.multiple_content[2].file.read() == b"Content 3"
            assert attachment.multiple_content[3].file.read() == b"Content 4"
            assert attachment.multiple_content[4].file.read() == b"Content 5"

    async def test_edit_existing_multiple_content_add_element_rollback(
        self, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Multiple content add element rollback",
                    multiple_content=[b"Content 1", b"Content 2"],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name
                    == "Multiple content add element rollback"
                )
            ).scalar_one()
            attachment.multiple_content += [b"Content 3", b"Content 4"]
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert len(attachment.multiple_content) == 4
            path3 = attachment.multiple_content[2].path
            path4 = attachment.multiple_content[3].path

            storage_service: StorageService = app.injector.get(StorageService)

            assert storage_service.get(path3) is not None
            assert storage_service.get(path4) is not None
            session.rollback()

            assert len(attachment.multiple_content) == 2

            for path in (path3, path4):
                with pytest.raises(ObjectDoesNotExistError):
                    storage_service.get(path)

    async def test_edit_existing_multiple_content_remove_element(
        self, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Multiple content remove element",
                    multiple_content=[
                        b"Content 1",
                        b"Content 2",
                        b"Content 3",
                        b"Content 4",
                        b"Content 5",
                    ],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name == "Multiple content remove element"
                )
            ).scalar_one()
            first_removed = attachment.multiple_content.pop(1)
            second_removed = attachment.multiple_content[3]
            attachment.multiple_content.remove(second_removed)
            third_removed = attachment.multiple_content[2]
            del attachment.multiple_content[2]
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert len(attachment.multiple_content) == 2
            assert attachment.multiple_content[0].file.read() == b"Content 1"
            assert attachment.multiple_content[1].file.read() == b"Content 3"

            storage_service: StorageService = app.injector.get(StorageService)

            for file in (first_removed, second_removed, third_removed):
                with pytest.raises(ObjectDoesNotExistError):
                    storage_service.get(file.path)

    async def test_edit_existing_multiple_content_remove_element_rollback(
        self, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Multiple content remove element rollback",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name
                    == "Multiple content remove element rollback"
                )
            ).scalar_one()
            attachment.multiple_content.pop(0)
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert len(attachment.multiple_content) == 2
            assert attachment.multiple_content[0].file.read() == b"Content 2"
            assert attachment.multiple_content[1].file.read() == b"Content 3"
            session.rollback()
            assert len(attachment.multiple_content) == 3
            assert attachment.multiple_content[0].file.read() == b"Content 1"
            assert attachment.multiple_content[1].file.read() == b"Content 2"
            assert attachment.multiple_content[2].file.read() == b"Content 3"

    async def test_edit_existing_multiple_content_replace_element(
        self, fake_file, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Multiple content replace",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name == "Multiple content replace"
                )
            ).scalar_one()
            before_replaced_path = attachment.multiple_content[1].path
            attachment.multiple_content[1] = b"Content 2 replaced"
            session.add(attachment)
            session.commit()
            session.refresh(attachment)

            assert attachment.multiple_content[1].file.read() == b"Content 2 replaced"

            storage_service: StorageService = app.injector.get(StorageService)

            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get(before_replaced_path)

    async def test_edit_existing_multiple_content_replace_element_rollback(
        self, fake_file, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Multiple content replace rollback",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name == "Multiple content replace rollback"
                )
            ).scalar_one()
            attachment.multiple_content[1] = b"Content 2 replaced"
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert attachment.multiple_content[1].file.read() == b"Content 2 replaced"
            new_path = attachment.multiple_content[1].path
            session.rollback()
            assert attachment.multiple_content[1].file.read() == b"Content 2"

            storage_service: StorageService = app.injector.get(StorageService)

            with pytest.raises(ObjectDoesNotExistError):
                storage_service.get(new_path)

    async def test_delete_existing_multiple_content(self, fake_file, app_setup) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Deleting multiple content",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name == "Deleting multiple content"
                )
            ).scalar_one()
            storage_service: StorageService = app.injector.get(StorageService)

            file_ids = [f.file_id for f in attachment.multiple_content]
            for file_id in file_ids:
                assert storage_service.get_container().get_object(file_id) is not None
            session.delete(attachment)
            session.commit()
            for file_id in file_ids:
                with pytest.raises(ObjectDoesNotExistError):
                    storage_service.get_container().get_object(file_id)

    async def test_delete_existing_multiple_content_rollback(
        self, fake_file, app_setup
    ) -> None:
        async with self.init_app(app_setup) as (app, db_service, session):
            session.add(
                AttachmentMultipleFields(
                    name="Deleting multiple content rollback",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                model.select(AttachmentMultipleFields).where(
                    AttachmentMultipleFields.name
                    == "Deleting multiple content rollback"
                )
            ).scalar_one()

            storage_service: StorageService = app.injector.get(StorageService)

            file_ids = [f.file_id for f in attachment.multiple_content]
            for file_id in file_ids:
                assert storage_service.get_container().get_object(file_id) is not None
            session.delete(attachment)
            session.flush()
            session.rollback()
            for file_id in file_ids:
                assert storage_service.get_container().get_object(file_id) is not None
