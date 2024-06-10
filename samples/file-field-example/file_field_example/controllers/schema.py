import typing as t

import ellar.common as ecm
from ellar.app import current_injector
from ellar.core import Request
from ellar.pydantic import model_validator
from pydantic import HttpUrl

from ellar_sql.model.mixins import ModelDataExportMixin
from ellar_sql.model.typeDecorator.file import File


class BookSchema(ecm.Serializer):
    id: int
    title: str
    cover: HttpUrl

    thumbnail: HttpUrl

    @model_validator(mode="before")
    def cover_validate_before(cls, values) -> t.Any:
        req: Request = (
            current_injector.get(ecm.IExecutionContext)
            .switch_to_http_connection()
            .get_request()
        )
        values = values.dict() if isinstance(values, ModelDataExportMixin) else values

        cover: File = values["cover"]

        values["cover"] = str(
            req.url_for("storage:download", path=cover["path"])
        )  # from ellar_storage.StorageController
        values["thumbnail"] = str(
            req.url_for("storage:download", path=cover["files"][1])
        )  # from ellar_storage.StorageController

        return values


class ArticleSchema(ecm.Serializer):
    id: int
    title: str
    documents: t.List[HttpUrl]

    @model_validator(mode="before")
    def model_validate_before(cls, values) -> t.Any:
        req: Request = (
            current_injector.get(ecm.IExecutionContext)
            .switch_to_http_connection()
            .get_request()
        )
        values = values.dict() if isinstance(values, ModelDataExportMixin) else values

        values["documents"] = [
            str(req.url_for("storage:download", path=item["path"]))
            for item in values["documents"]
        ]

        return values


class AttachmentSchema(ecm.Serializer):
    id: int
    name: str
    content: HttpUrl

    @model_validator(mode="before")
    def model_validate_before(cls, values) -> t.Any:
        req: Request = (
            current_injector.get(ecm.IExecutionContext)
            .switch_to_http_connection()
            .get_request()
        )
        values = values.dict() if isinstance(values, ModelDataExportMixin) else values

        values["content"] = str(
            req.url_for("storage:download", path=values["content"]["path"])
        )
        return values
