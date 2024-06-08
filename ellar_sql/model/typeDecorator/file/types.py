import typing as t

from ellar.pydantic.types import Validator
from sqlalchemy_file.types import FileField as BaseFileField

from ellar_sql.constant import DEFAULT_STORAGE_PLACEHOLDER

from .file import File
from .processors import Processor, ThumbnailGenerator
from .validators import ImageValidator


class FileField(BaseFileField):
    def __init__(
        self,
        *args: t.Tuple[t.Any],
        upload_storage: t.Optional[str] = None,
        validators: t.Optional[t.List[Validator]] = None,
        processors: t.Optional[t.List[Processor]] = None,
        upload_type: t.Type[File] = File,
        multiple: t.Optional[bool] = False,
        extra: t.Optional[t.Dict[str, t.Any]] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        **kwargs: t.Dict[str, t.Any],
    ) -> None:
        """Parameters:
        upload_storage: storage to use
        validators: List of validators to apply
        processors: List of validators to apply
        upload_type: File class to use, could be
        used to set custom File class
        multiple: Use this to save multiple files
        extra: Extra attributes (driver specific)
        headers: Additional request headers,
        such as CORS headers. For example:
        headers = {'Access-Control-Allow-Origin': 'http://mozilla.com'}.
        """
        super().__init__(
            *args,
            processors=processors,
            validators=validators,
            headers=headers,
            upload_type=upload_type,
            multiple=multiple,
            extra=extra,
            **kwargs,  # type: ignore[arg-type]
        )
        self.upload_storage = upload_storage or DEFAULT_STORAGE_PLACEHOLDER


class ImageField(FileField):
    def __init__(
        self,
        *args: t.Tuple[t.Any],
        upload_storage: t.Optional[str] = None,
        thumbnail_size: t.Optional[t.Tuple[int, int]] = None,
        image_validator: t.Optional[ImageValidator] = None,
        validators: t.Optional[t.List[Validator]] = None,
        processors: t.Optional[t.List[Processor]] = None,
        upload_type: t.Type[File] = File,
        multiple: t.Optional[bool] = False,
        extra: t.Optional[t.Dict[str, str]] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        **kwargs: t.Dict[str, t.Any],
    ) -> None:
        """Parameters
        upload_storage: storage to use
        image_validator: ImageField use default image
        validator, Use this property to customize it.
        thumbnail_size: If set, a thumbnail will be generated
        from original image using [ThumbnailGenerator]
        [sqlalchemy_file.processors.ThumbnailGenerator]
        validators: List of additional validators to apply
        processors: List of validators to apply
        upload_type: File class to use, could be
        used to set custom File class
        multiple: Use this to save multiple files
        extra: Extra attributes (driver specific).
        """
        if validators is None:
            validators = []
        if image_validator is None:
            image_validator = ImageValidator()
        if thumbnail_size is not None:
            if processors is None:
                processors = []
            processors.append(ThumbnailGenerator(thumbnail_size))
        validators.append(image_validator)
        super().__init__(
            *args,
            upload_storage=upload_storage,
            validators=validators,
            processors=processors,
            upload_type=upload_type,
            multiple=multiple,
            extra=extra,
            headers=headers,
            **kwargs,
        )
