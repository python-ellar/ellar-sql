import os
from pathlib import Path

from ellar.app import App
from ellar.common import (
    IApplicationStartup,
    IExecutionContext,
    JSONResponse,
    Module,
    Response,
    exception_handler,
)
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule
from ellar_storage import Provider, StorageModule, get_driver

from ellar_sql import EllarSQLModule, EllarSQLService

from .controllers import ArticlesController, AttachmentController, BooksController

BASE_DIRS = Path(__file__).parent

modules = [
    HomeModule,
    StorageModule.setup(
        files={
            "driver": get_driver(Provider.LOCAL),
            "options": {"key": os.path.join(BASE_DIRS, "media")},
        },
        bookstore={
            "driver": get_driver(Provider.LOCAL),
            "options": {"key": os.path.join(BASE_DIRS, "media")},
        },
        documents={
            "driver": get_driver(Provider.LOCAL),
            "options": {"key": os.path.join(BASE_DIRS, "media")},
        },
        default="files",
    ),
    EllarSQLModule.setup(
        databases="sqlite:///project.db",
        models=["file_field_example.models"],
        migration_options={"directory": os.path.join(BASE_DIRS, "migrations")},
    ),
]


@Module(
    modules=modules,
    controllers=[BooksController, AttachmentController, ArticlesController],
)
class ApplicationModule(ModuleBase, IApplicationStartup):
    async def on_startup(self, app: App) -> None:
        db_service = app.injector.get(EllarSQLService)
        db_service.create_all()

    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."}, status_code=404)
