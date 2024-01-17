import json
import time
import typing as t
import uuid
from abc import abstractmethod

import sqlalchemy as sa
from ellar.common import UploadFile
from ellar.core.files.storages import BaseStorage
from ellar.core.files.storages.utils import get_valid_filename

from ellar_sql.model.typeDecorator.exceptions import (
    ContentTypeValidationError,
    InvalidFileError,
    MaximumAllowedFileLengthError,
)
from ellar_sql.model.typeDecorator.mimetypes import (
    guess_extension,
    magic_mime_from_buffer,
)
from ellar_sql.model.utils import get_length

from .file_info import FileObject

T = t.TypeVar("T", bound="FileObject")


class FileFieldBase(t.Generic[T]):
    @property
    @abstractmethod
    def file_object_type(self) -> t.Type[T]:
        ...

    def load_dialect_impl(self, dialect: sa.Dialect) -> t.Any:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(sa.String())
        else:
            return dialect.type_descriptor(sa.JSON())

    def __init__(
        self,
        *args: t.Any,
        storage: t.Optional[BaseStorage] = None,
        allowed_content_types: t.Optional[t.List[str]] = None,
        max_size: t.Optional[int] = None,
        **kwargs: t.Any,
    ):
        if allowed_content_types is None:
            allowed_content_types = []
        super().__init__(*args, **kwargs)

        self._storage = storage
        self._allowed_content_types = allowed_content_types
        self._max_size = max_size

    @property
    def storage(self) -> BaseStorage:
        assert self._storage
        return self._storage

    def validate(self, file: T) -> None:
        if (
            self._allowed_content_types
            and file.content_type not in self._allowed_content_types
        ):
            raise ContentTypeValidationError(
                file.content_type, self._allowed_content_types
            )
        if self._max_size and file.file_size > self._max_size:
            raise MaximumAllowedFileLengthError(self._max_size)

        self.storage.validate_file_name(file.filename)

    def load_from_str(self, data: str) -> T:
        data_dict = t.cast(t.Dict[str, t.Any], json.loads(data))
        return self.load(data_dict)

    def load(self, data: t.Dict[str, t.Any]) -> T:
        if "service_name" in data:
            data.pop("service_name")
        return self.file_object_type(storage=self.storage, **data)

    def _guess_content_type(self, file: t.IO) -> str:  # type:ignore[type-arg]
        content = file.read(1024)

        if isinstance(content, str):
            content = str.encode(content)

        file.seek(0)

        return magic_mime_from_buffer(content)

    def get_extra_file_initialization_context(
        self, file: UploadFile
    ) -> t.Dict[str, t.Any]:
        return {}

    def convert_to_file_object(self, file: UploadFile) -> T:
        unique_name = str(uuid.uuid4())

        original_filename = file.filename or unique_name

        # use python magic to get the content type
        content_type = self._guess_content_type(file.file) or ""
        extension = guess_extension(content_type)
        file_size = get_length(file.file)
        if extension:
            saved_filename = (
                f"{original_filename[:-len(extension)]}_{unique_name[:-8]}{extension}"
            )
        else:
            saved_filename = f"{unique_name[:-8]}_{original_filename}"
        saved_filename = get_valid_filename(saved_filename)

        init_kwargs = self.get_extra_file_initialization_context(file)
        init_kwargs.update(
            storage=self.storage,
            original_filename=original_filename,
            uploaded_on=int(time.time()),
            content_type=content_type,
            extension=extension,
            file_size=file_size,
            saved_filename=saved_filename,
        )
        return self.file_object_type(**init_kwargs)

    def process_bind_param_action(
        self, value: t.Optional[t.Any], dialect: sa.Dialect
    ) -> t.Optional[t.Union[str, t.Dict[str, t.Any]]]:
        if value is None:
            return value

        if isinstance(value, UploadFile):
            value.file.seek(0)  # make sure we are always at the beginning
            file_obj = self.convert_to_file_object(value)
            self.validate(file_obj)

            self.storage.put(file_obj.filename, value.file)
            value = file_obj

        if isinstance(value, FileObject):
            if dialect.name == "sqlite":
                return json.dumps(value.to_dict())
            return value.to_dict()

        raise InvalidFileError(f"{value} is not supported")

    def process_result_value_action(
        self, value: t.Optional[t.Any], dialect: sa.Dialect
    ) -> t.Optional[t.Union[str, t.Dict[str, t.Any], t.Any]]:
        if value is None:
            return value
        else:
            if isinstance(value, str):
                value = self.load_from_str(value)
            elif isinstance(value, dict):
                value = self.load(value)
            return value
