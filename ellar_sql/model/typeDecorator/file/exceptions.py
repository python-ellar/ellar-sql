from sqlalchemy_file.exceptions import ContentTypeValidationError  # noqa
from sqlalchemy_file.exceptions import InvalidImageError  # noqa
from sqlalchemy_file.exceptions import DimensionValidationError  # noqa
from sqlalchemy_file.exceptions import AspectRatioValidationError  # noqa
from sqlalchemy_file.exceptions import SizeValidationError  # noqa
from sqlalchemy_file.exceptions import ValidationError

from ellar.common import IExecutionContext
from ellar.core.exceptions import as_exception_handler


# Register to application config.EXCEPTION_HANDLERS to add exception handler for sqlalchemy-file
@as_exception_handler(ValidationError)
async def FileExceptionHandler(ctx: IExecutionContext, exc: ValidationError):
    app_config = ctx.get_app().config
    return app_config.DEFAULT_JSON_CLASS(
        {"message": exc.msg, "key": exc.key},
        status_code=400,
    )
