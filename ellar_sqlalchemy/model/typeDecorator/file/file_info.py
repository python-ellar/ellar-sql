import typing as t

from ellar.core.files.storages import BaseStorage

T = t.TypeVar("T", bound="FileObject")


class FileObject:
    def __init__(
        self,
        *,
        storage: BaseStorage,
        original_filename: str,
        uploaded_on: int,
        content_type: str,
        saved_filename: str,
        extension: str,
        file_size: int,
    ) -> None:
        self._storage = storage
        self.original_filename = original_filename
        self.uploaded_on = uploaded_on
        self.content_type = content_type
        self.filename = saved_filename
        self.extension = extension
        self.file_size = file_size

    def locate(self) -> str:
        return self._storage.locate(self.filename)

    def open(self) -> t.IO:  # type:ignore[type-arg]
        return self._storage.open(self.filename)

    def to_dict(self) -> t.Dict[str, t.Any]:
        return {
            "original_filename": self.original_filename,
            "uploaded_on": self.uploaded_on,
            "content_type": self.content_type,
            "extension": self.extension,
            "file_size": self.file_size,
            "saved_filename": self.filename,
            "service_name": self._storage.service_name(),
        }

    def __str__(self) -> str:
        return f"filename={self.filename}, content_type={self.content_type}, file_size={self.file_size}"

    def __repr__(self) -> str:
        return str(self)
