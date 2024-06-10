from sqlalchemy_file.exceptions import ContentTypeValidationError  # noqa
from sqlalchemy_file.exceptions import InvalidImageError  # noqa
from sqlalchemy_file.exceptions import DimensionValidationError  # noqa
from sqlalchemy_file.exceptions import AspectRatioValidationError  # noqa
from sqlalchemy_file.exceptions import SizeValidationError  # noqa
from sqlalchemy_file.exceptions import ValidationError

from ellar.common import IExecutionContext
from ellar.common.exceptions import CallableExceptionHandler


def _exception_handlers(ctx: IExecutionContext, exc: ValidationError):
    app_config = ctx.get_app().config
    return app_config.DEFAULT_JSON_CLASS(
        {"message": exc.msg, "key": exc.key},
        status_code=400,
    )


# Register to application config.EXCEPTION_HANDLERS to add exception handler for sqlalchemy-file
FileExceptionHandler = CallableExceptionHandler(
    exc_class_or_status_code=ValidationError,
    callable_exception_handler=_exception_handlers,
)
