import typing as t
from io import SEEK_END, BytesIO

import sqlalchemy as sa
from ellar.common import UploadFile
from ellar.core.files.storages import BaseStorage
from PIL import Image

from ..exceptions import InvalidImageOperationError
from ..file import FileFieldBase
from .crop_info import CroppingDetails
from .file_info import ImageFileObject


class ImageFileField(FileFieldBase[ImageFileObject], sa.TypeDecorator):  # type: ignore[type-arg]
    """
    Provide SqlAlchemy TypeDecorator for Image files
    ## Basic Usage

    class MyTable(Base):
        image: ImageFileField.FileObject = sa.Column(
            ImageFileField(storage=FileSystemStorage('path/to/save/files', max_size=10*MB),
            nullable=True
        )

    def route(file: File[UploadFile]):
        session = SessionLocal()
        my_table_model = MyTable(image=file)
        session.add(my_table_model)
        session.commit()
        return my_table_model.image.to_dict()

    ## Cropping
    Image file also provides cropping capabilities which can be defined in the column or when saving the image data.

    fs = FileSystemStorage('path/to/save/files')
    class MyTable(Base):
        image = sa.Column(ImageFileField(storage=fs, crop=CroppingDetails(x=100, y=200, height=400, width=400)), nullable=True)

    OR
    def route(file: File[UploadFile]):
        session = SessionLocal()
        my_table_model = MyTable(
            image=(file, CroppingDetails(x=100, y=200, height=400, width=400)),
        )

    """

    impl = sa.JSON

    def __init__(
        self,
        *args: t.Any,
        storage: BaseStorage,
        max_size: t.Optional[int] = None,
        crop: t.Optional[CroppingDetails] = None,
        **kwargs: t.Any,
    ):
        kwargs.setdefault("allowed_content_types", ["image/jpeg", "image/png"])
        super().__init__(*args, storage=storage, max_size=max_size, **kwargs)
        self.crop = crop

    @property
    def file_object_type(self) -> t.Type[ImageFileObject]:
        return ImageFileObject

    def process_bind_param(
        self, value: t.Optional[t.Any], dialect: sa.Dialect
    ) -> t.Any:
        return self.process_bind_param_action(value, dialect)

    def process_result_value(
        self, value: t.Optional[t.Any], dialect: sa.Dialect
    ) -> t.Any:
        return self.process_result_value_action(value, dialect)

    def get_extra_file_initialization_context(
        self, file: UploadFile
    ) -> t.Dict[str, t.Any]:
        try:
            with Image.open(file.file) as image:
                width, height = image.size
                return {"width": width, "height": height}
        except Exception:
            return {"width": None, "height": None}

    def crop_image_with_box_sizing(
        self, file: UploadFile, crop: t.Optional[CroppingDetails] = None
    ) -> UploadFile:
        crop_info = crop or self.crop
        img = Image.open(file.file)
        (
            height,
            width,
            x,
            y,
        ) = (
            crop_info.height,
            crop_info.width,
            crop_info.x,
            crop_info.y,
        )
        left = x
        top = y
        right = x + width
        bottom = y + height

        crop_box = (left, top, right, bottom)

        img_res = img.crop(box=crop_box)
        temp_thumb = BytesIO()
        img_res.save(temp_thumb, img.format)
        # Go to the end of the stream.
        temp_thumb.seek(0, SEEK_END)

        # Get the current position, which is now at the end.
        # We can use this as the size.
        size = temp_thumb.tell()
        temp_thumb.seek(0)

        content = UploadFile(
            file=temp_thumb, filename=file.filename, size=size, headers=file.headers
        )
        return content

    def process_bind_param_action(
        self, value: t.Optional[t.Any], dialect: sa.Dialect
    ) -> t.Optional[t.Union[str, t.Dict[str, t.Any]]]:
        if isinstance(value, tuple):
            file, crop_data = value
            if not isinstance(file, UploadFile) or not isinstance(
                crop_data, CroppingDetails
            ):
                raise InvalidImageOperationError(
                    "Invalid data was provided for ImageFileField. "
                    "Accept values: UploadFile or (UploadFile, CroppingDetails)"
                )
            new_file = self.crop_image_with_box_sizing(file=file, crop=crop_data)
            return super().process_bind_param_action(new_file, dialect)

        if isinstance(value, UploadFile):
            if self.crop:
                return super().process_bind_param_action(
                    self.crop_image_with_box_sizing(value), dialect
                )
        return super().process_bind_param_action(value, dialect)
