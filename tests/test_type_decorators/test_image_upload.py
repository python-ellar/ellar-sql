import os
import uuid
from pathlib import Path

import pytest
import sqlalchemy.exc as sa_exc
from ellar.common.datastructures import ContentFile, UploadFile
from ellar.core.files import storages
from starlette.datastructures import Headers

from ellar_sql import model
from ellar_sql.model.utils import get_length

fixtures_dir = Path(__file__).parent / "fixtures"


def get_image_upload(file, *, filename):
    return UploadFile(
        file,
        filename=filename,
        size=get_length(file),
        headers=Headers({"content-type": ""}),
    )


def serialize_file_data(file):
    keys = {
        "original_filename",
        "content_type",
        "extension",
        "file_size",
        "service_name",
        "height",
        "width",
    }
    return {k: v for k, v in file.to_dict().items() if k in keys}


def test_image_column_type(db_service, ignore_base, tmp_path):
    path = str(tmp_path / "images")
    fs = storages.FileSystemStorage(path)

    class Image(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        image: model.Mapped[model.ImageFileObject] = model.mapped_column(
            "image", model.ImageFileField(storage=fs), nullable=False
        )

    with open(fixtures_dir / "image.png", mode="rb+") as fp:
        db_service.create_all()
        session = db_service.session_factory()
        session.add(Image(image=get_image_upload(filename="image.png", file=fp)))
        session.commit()

    file: Image = session.execute(model.select(Image)).scalar()

    data = serialize_file_data(file.image)
    assert data == {
        "content_type": "image/png",
        "extension": ".png",
        "file_size": 1590279,
        "height": 1080,
        "original_filename": "image.png",
        "service_name": "local",
        "width": 1080,
    }

    assert os.listdir(path)[0].split(".")[1] == "png"


def test_image_file_with_cropping_details_set_on_column(
    db_service, ignore_base, tmp_path
):
    fs = storages.FileSystemStorage(str(tmp_path / "images"))

    class Image2(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        image: model.Mapped[model.ImageFileObject] = model.mapped_column(
            "image",
            model.ImageFileField(
                storage=fs,
                crop=model.CroppingDetails(x=100, y=200, height=400, width=400),
            ),
            nullable=False,
        )

    with open(fixtures_dir / "image.png", mode="rb+") as fp:
        db_service.create_all()
        session = db_service.session_factory()
        session.add(Image2(image=get_image_upload(filename="image.png", file=fp)))
        session.commit()

    image_2: Image2 = session.execute(model.select(Image2)).scalar()

    data = serialize_file_data(image_2.image)
    assert data == {
        "content_type": "image/png",
        "extension": ".png",
        "file_size": 108477,
        "height": 400,
        "original_filename": "image.png",
        "service_name": "local",
        "width": 400,
    }


def test_image_file_with_cropping_details_on_set(db_service, ignore_base, tmp_path):
    fs = storages.FileSystemStorage(str(tmp_path / "images"))

    class Image3(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        image: model.Mapped[model.ImageFileObject] = model.mapped_column(
            "image", model.ImageFileField(storage=fs), nullable=False
        )

    db_service.create_all()
    session = db_service.session_factory()

    with open(fixtures_dir / "image.png", mode="rb+") as fp:
        file = get_image_upload(filename="image.png", file=fp)
        image_input = (file, model.CroppingDetails(x=100, y=200, height=400, width=400))

        session.add(Image3(image=image_input))
        session.commit()

    image_3: Image3 = session.execute(model.select(Image3)).scalar()

    data = serialize_file_data(image_3.image)
    assert data == {
        "content_type": "image/png",
        "extension": ".png",
        "file_size": 108477,
        "height": 400,
        "original_filename": "image.png",
        "service_name": "local",
        "width": 400,
    }


def test_image_file_with_cropping_details_override(db_service, ignore_base, tmp_path):
    fs = storages.FileSystemStorage(str(tmp_path / "images"))

    class Image4(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        image: model.Mapped[model.ImageFileObject] = model.mapped_column(
            "image",
            model.ImageFileField(
                storage=fs,
                crop=model.CroppingDetails(x=100, y=200, height=400, width=400),
            ),
            nullable=False,
        )

    db_service.create_all()
    session = db_service.session_factory()

    with open(fixtures_dir / "image.png", mode="rb+") as fp:
        file = get_image_upload(filename="image.png", file=fp)
        image_input = (file, model.CroppingDetails(x=100, y=200, height=300, width=300))

        session.add(Image4(image=image_input))
        session.commit()

    image_4: Image4 = session.execute(model.select(Image4)).scalar()

    data = serialize_file_data(image_4.image)
    assert data == {
        "content_type": "image/png",
        "extension": ".png",
        "file_size": 54508,
        "height": 300,
        "original_filename": "image.png",
        "service_name": "local",
        "width": 300,
    }


def test_image_column_invalid_set(db_service, ignore_base, tmp_path):
    fs = storages.FileSystemStorage(str(tmp_path / "files"))

    class Image3(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        image: model.Mapped[model.ImageFileObject] = model.mapped_column(
            "image", model.ImageFileField(storage=fs), nullable=False
        )

    db_service.create_all()
    session = db_service.session_factory()

    with pytest.raises(sa_exc.StatementError) as stmt_exc:
        invalid_input = (ContentFile(b"Invalid Set"), {})
        session.add(Image3(image=invalid_input))
        session.commit()
    assert str(stmt_exc.value.orig) == (
        "Invalid data was provided for ImageFileField. "
        "Accept values: UploadFile or (UploadFile, CroppingDetails)"
    )


def test_image_column_invalid_set_case_2(db_service, ignore_base, tmp_path):
    fs = storages.FileSystemStorage(str(tmp_path / "files"))

    class Image3(model.Model):
        id: model.Mapped[uuid.uuid4] = model.mapped_column(
            "id", model.Integer(), nullable=False, unique=True, primary_key=True
        )
        image: model.Mapped[model.ImageFileObject] = model.mapped_column(
            "image", model.ImageFileField(storage=fs), nullable=False
        )

    db_service.create_all()
    session = db_service.session_factory()

    with pytest.raises(sa_exc.StatementError) as stmt_exc:
        session.add(Image3(image=ContentFile(b"Not an image")))
        session.commit()
    assert str(stmt_exc.value.orig) == (
        "Content type is not supported text/plain. Valid options are: image/jpeg, image/png"
    )
