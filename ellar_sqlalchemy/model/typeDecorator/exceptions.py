import typing as t


class ContentTypeValidationError(ValueError):
    def __init__(
        self,
        content_type: t.Optional[str] = None,
        valid_content_types: t.Optional[t.List[str]] = None,
    ) -> None:
        if content_type is None:
            message = "Content type is not provided. "
        else:
            message = "Content type is not supported %s. " % content_type

        if valid_content_types:
            message += "Valid options are: %s" % ", ".join(valid_content_types)

        super().__init__(message)


class InvalidFileError(ValueError):
    pass


class InvalidImageOperationError(ValueError):
    pass


class MaximumAllowedFileLengthError(ValueError):
    def __init__(self, max_length: int) -> None:
        super().__init__("Cannot store files larger than: %d bytes" % max_length)
