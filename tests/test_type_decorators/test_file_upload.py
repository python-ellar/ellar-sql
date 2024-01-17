import os
import uuid
from io import BytesIO
from unittest.mock import patch

import pytest
import sqlalchemy.exc as sa_exc
from ellar.common.datastructures import ContentFile, UploadFile
from ellar.core.files import storages
from starlette.datastructures import Headers

from ellar_sql import model
from ellar_sql.model.utils import MB


def serialize_file_data(file):
    keys = {
        "original_filename",
        "content_type",
        "extension",
        "file_size",
        "service_name",
    }
    return {k: v for k, v in file.to_dict().items() if k in keys}


def test_file_column_type(db_service, ignore_base, tmp_path):
    path = str(tmp_path / "files")
    fs = storages.FileSystemStorage(path)

    class File(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        file: model.Mapped[model.FileObject] = model.mapped_column(
            "file", model.FileField(storage=fs), nullable=False
        )

    db_service.create_all()
    session = db_service.session_factory()
    session.add(File(file=ContentFile(b"Testing file column type", name="text.txt")))
    session.commit()

    file: File = session.execute(model.select(File)).scalar()
    assert "content_type=text/plain" in repr(file.file)

    data = serialize_file_data(file.file)
    assert data == {
        "content_type": "text/plain",
        "extension": ".txt",
        "file_size": 24,
        "original_filename": "text.txt",
        "service_name": "local",
    }

    assert os.listdir(path)[0].split(".")[1] == "txt"


def test_file_column_invalid_file_extension(db_service, ignore_base, tmp_path):
    fs = storages.FileSystemStorage(str(tmp_path / "files"))

    class File(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        file: model.Mapped[model.FileObject] = model.mapped_column(
            "file",
            model.FileField(storage=fs, allowed_content_types=["application/pdf"]),
            nullable=False,
        )

    with pytest.raises(sa_exc.StatementError) as stmt_exc:
        db_service.create_all()
        session = db_service.session_factory()
        session.add(
            File(file=ContentFile(b"Testing file column type", name="text.txt"))
        )
        session.commit()
    assert (
        str(stmt_exc.value.orig)
        == "Content type is not supported text/plain. Valid options are: application/pdf"
    )


@patch(
    "ellar_sql.model.typeDecorator.file.base.magic_mime_from_buffer",
    return_value=None,
)
def test_file_column_invalid_file_extension_case_2(
    mock_buffer, db_service, ignore_base, tmp_path
):
    fs = storages.FileSystemStorage(str(tmp_path / "files"))

    class File(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        file: model.Mapped[model.FileObject] = model.mapped_column(
            "file",
            model.FileField(storage=fs, allowed_content_types=["application/pdf"]),
            nullable=False,
        )

    with pytest.raises(sa_exc.StatementError) as stmt_exc:
        db_service.create_all()
        session = db_service.session_factory()
        session.add(
            File(
                file=UploadFile(
                    BytesIO(b"Testing file column type"),
                    size=24,
                    filename="test.txt",
                    headers=Headers({"content-type": ""}),
                )
            )
        )
        session.commit()
    assert mock_buffer.called
    assert (
        str(stmt_exc.value.orig)
        == "Content type is not supported . Valid options are: application/pdf"
    )


@patch("ellar_sql.model.typeDecorator.file.base.get_length", return_value=MB * 7)
def test_file_column_invalid_file_size_case_2(
    mock_buffer, db_service, ignore_base, tmp_path
):
    fs = storages.FileSystemStorage(str(tmp_path / "files"))

    class File(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        file: model.Mapped[model.FileObject] = model.mapped_column(
            "file", model.FileField(storage=fs, max_size=MB * 6), nullable=False
        )

    with pytest.raises(sa_exc.StatementError) as stmt_exc:
        db_service.create_all()
        session = db_service.session_factory()
        session.add(File(file=ContentFile(b"Testing File Size Validation")))
        session.commit()
    assert mock_buffer.called
    assert str(stmt_exc.value.orig) == "Cannot store files larger than: 6291456 bytes"


def test_file_column_invalid_set(db_service, ignore_base, tmp_path):
    fs = storages.FileSystemStorage(str(tmp_path / "files"))

    class File(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        file: model.Mapped[model.FileObject] = model.mapped_column(
            "file", model.FileField(storage=fs, max_size=MB * 6), nullable=False
        )

    db_service.create_all()
    session = db_service.session_factory()
    with pytest.raises(sa_exc.StatementError) as stmt_exc:
        session.add(File(file={}))
        session.commit()

    assert str(stmt_exc.value.orig) == "{} is not supported"
