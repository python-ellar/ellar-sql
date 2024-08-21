from ellar.common import (
    Module,
)
from ellar.core import LazyModuleImport as lazyLoad
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule


@Module(modules=[HomeModule, lazyLoad("db.module:DbModule")])
class ApplicationModule(ModuleBase):
    pass
