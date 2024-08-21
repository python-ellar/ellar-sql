import typing as t

import ellar.common as ecm
from ellar.core import Request, current_injector
from ellar.pydantic import model_validator
from pydantic import HttpUrl


class FileItem(ecm.Serializer):
    url: HttpUrl

    @model_validator(mode="before")
    def cover_validate_before(cls, values) -> t.Any:
        req: Request = (
            current_injector.get(ecm.IExecutionContext)
            .switch_to_http_connection()
            .get_request()
        )
        values_ = dict(values)

        values_["url"] = str(
            req.url_for("storage:download", path=values.path)
        )  # from ellar_storage.StorageController

        if values.thumbnail:
            values_["thumbnail"] = str(
                req.url_for("storage:download", path=values.thumbnail["path"])
            )  # from ellar_storage.StorageController

        return values_


class BookCover(FileItem):
    thumbnail: HttpUrl


class BookSchema(ecm.Serializer):
    id: int
    title: str

    cover: BookCover


class ArticleSchema(ecm.Serializer):
    id: int
    title: str
    documents: t.List[FileItem]


class AttachmentSchema(ecm.Serializer):
    id: int
    name: str
    content: FileItem
