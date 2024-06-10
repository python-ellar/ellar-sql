import typing as t
import uuid
import warnings
from datetime import datetime

from ellar.app import current_injector
from ellar.common.compatible import AttributeDictAccessMixin
from ellar_storage import StorageService, StoredFile
from sqlalchemy_file.file import File as BaseFile
from starlette.datastructures import UploadFile

from ellar_sql.constant import DEFAULT_STORAGE_PLACEHOLDER


class File(BaseFile, AttributeDictAccessMixin):
    """Takes a file as content and uploads it to the appropriate storage
    according to the attached Column and file information into the
    database as JSON.

    Default attributes provided for all ``File`` include:

    Attributes:
        filename (str): This is the name of the uploaded file
        file_id: This is the generated UUID for the uploaded file
        upload_storage: Name of the storage used to save the uploaded file
        path: This is a combination of `upload_storage` and `file_id` separated by
                        `/`. This will be used later to retrieve the file
        content_type:   This is the content type of the uploaded file
        uploaded_at (datetime):    This is the upload date in ISO format
        url (str):            CDN url of the uploaded file
        file:           Only available for saved content, internally call
                      [StorageManager.get_file()][sqlalchemy_file.storage.StorageManager.get_file]
                      on path and return an instance of `StoredFile`
    """

    filename: str
    file_id: str

    upload_storage: str
    path: str

    content_type: str
    uploaded_at: str
    url: str

    saved: bool
    size: int

    files: t.List[str]

    def __init__(
        self,
        content: t.Any = None,
        filename: t.Optional[str] = None,
        content_type: t.Optional[str] = None,
        content_path: t.Optional[str] = None,
        **kwargs: t.Dict[str, t.Any],
    ) -> None:
        if isinstance(content, UploadFile):
            filename = content.filename
            content_type = content.content_type

            kwargs.setdefault("headers", dict(content.headers))

            content = content.file

        super().__init__(
            content=content,
            filename=filename,
            content_path=content_path,
            content_type=content_type,
            **kwargs,
        )

    def save_to_storage(self, upload_storage: t.Optional[str] = None) -> None:
        """Save current file into provided `upload_storage`."""
        storage_service = current_injector.get(StorageService)
        valid_upload_storage = storage_service.get_container(
            upload_storage
            if not upload_storage == DEFAULT_STORAGE_PLACEHOLDER
            else None
        ).name

        extra = self.get("extra", {})
        extra.update({"content_type": self.content_type})

        metadata = self.get("metadata", None)
        if metadata is not None:
            warnings.warn(
                'metadata attribute is deprecated. Use extra={"meta_data": ...} instead',
                DeprecationWarning,
                stacklevel=1,
            )
            extra.update({"meta_data": metadata})

        if extra.get("meta_data", None) is None:
            extra["meta_data"] = {}

        extra["meta_data"].update(
            {"filename": self.filename, "content_type": self.content_type}
        )
        stored_file = self.store_content(
            self.original_content,
            valid_upload_storage,
            extra=extra,
            headers=self.get("headers", None),
            content_path=self.content_path,
        )
        self["file_id"] = stored_file.name
        self["upload_storage"] = valid_upload_storage
        self["uploaded_at"] = datetime.utcnow().isoformat()
        self["path"] = f"{valid_upload_storage}/{stored_file.name}"
        self["url"] = stored_file.get_cdn_url()
        self["saved"] = True

    def store_content(  # type:ignore[override]
        self,
        content: t.Any,
        upload_storage: t.Optional[str] = None,
        name: t.Optional[str] = None,
        metadata: t.Optional[t.Dict[str, t.Any]] = None,
        extra: t.Optional[t.Dict[str, t.Any]] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        content_path: t.Optional[str] = None,
    ) -> StoredFile:
        """Store content into provided `upload_storage`
        with additional `metadata`. Can be used by processors
        to store additional files.
        """
        name = name or str(uuid.uuid4())
        storage_service = current_injector.get(StorageService)

        stored_file = storage_service.save_content(
            name=name,
            content=content,
            upload_storage=upload_storage,
            metadata=metadata,
            extra=extra,
            headers=headers,
            content_path=content_path,
        )
        self["files"].append(f"{upload_storage}/{name}")
        return stored_file

    @property
    def file(self) -> StoredFile:  # type:ignore[override]
        if self.get("saved", False):
            storage_service = current_injector.get(StorageService)
            return storage_service.get(self["path"])
        raise RuntimeError("Only available for saved file")

    def __missing__(self, name: t.Any) -> t.Any:
        if name in ["_frozen", "__clause_element__", "__pydantic_validator__"]:
            return super().__missing__(name)
        return None
