"""
@Module(
    controllers=[MyController],
    providers=[
        YourService,
        ProviderConfig(IService, use_class=AService),
        ProviderConfig(IFoo, use_value=FooService()),
    ],
    routers=(routerA, routerB)
    statics='statics',
    template='template_folder',
    # base_directory -> default is the `db` folder
)
class MyModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # for more complicated provider registrations
        pass

"""
from ellar.app import App
from ellar.common import Module, IApplicationStartup
from ellar.core import ModuleBase
from ellar.di import Container
from ellar_sqlalchemy import EllarSQLAlchemyModule, EllarSQLAlchemyService

from .controllers import DbController


@Module(
    controllers=[DbController],
    providers=[],
    routers=[],
    modules=[
        EllarSQLAlchemyModule.setup(
            databases={
                'default': 'sqlite:///project.db',
            },
            echo=True,
            migration_options={
                'directory': '__main__/migrations'
            },
            models=['db.models']
        )
    ]
)
class DbModule(ModuleBase, IApplicationStartup):
    """
    Db Module
    """

    async def on_startup(self, app: App) -> None:
        db_service = app.injector.get(EllarSQLAlchemyService)
        # db_service.create_all()

    def register_providers(self, container: Container) -> None:
        """for more complicated provider registrations, use container.register_instance(...) """