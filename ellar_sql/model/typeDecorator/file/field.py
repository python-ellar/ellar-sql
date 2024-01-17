import typing as t

import sqlalchemy as sa

from .base import FileFieldBase
from .file_info import FileObject


class FileField(FileFieldBase[FileObject], sa.TypeDecorator):  # type: ignore[type-arg]

    """
    Provide SqlAlchemy TypeDecorator for saving files
    ## Basic Usage

    fs = FileSystemStorage('path/to/save/files')

    class MyTable(Base):
        image: FileField.FileObject = sa.Column(
            ImageFileField(storage=fs, max_size=10*MB, allowed_content_type=["application/pdf"]),
            nullable=True
        )

    def route(file: File[UploadFile]):
        session = SessionLocal()
        my_table_model = MyTable(image=file)
        session.add(my_table_model)
        session.commit()
        return my_table_model.image.to_dict()

    """

    @property
    def file_object_type(self) -> t.Type[FileObject]:
        return FileObject

    impl = sa.JSON

    def process_bind_param(
        self, value: t.Optional[t.Any], dialect: sa.Dialect
    ) -> t.Any:
        return self.process_bind_param_action(value, dialect)

    def process_result_value(
        self, value: t.Optional[t.Any], dialect: sa.Dialect
    ) -> t.Any:
        return self.process_result_value_action(value, dialect)
