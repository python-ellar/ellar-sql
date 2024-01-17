import typing as t

import pytest
from ellar.testing import Test

from ellar_sql import EllarSQLModule, EllarSQLService, model
from ellar_sql.model.database_binds import __model_database_metadata__

super_classes_as_dataclass = [
    (
        (model.MappedAsDataclass, model.DeclarativeBase),
        {"metaclass": type(model.DeclarativeBase)},
    ),
    (
        (
            model.MappedAsDataclass,
            model.DeclarativeBaseNoMeta,
        ),
        {"metaclass": type(model.DeclarativeBaseNoMeta)},
    ),
]


test_classes = [
    object,
    (
        (model.DeclarativeBase,),
        {"metaclass": type(model.DeclarativeBase)},
    ),
    (
        (model.DeclarativeBaseNoMeta,),
        {"metaclass": type(model.DeclarativeBaseNoMeta)},
    ),
]


@pytest.fixture(params=test_classes)
def base_super_class(request: pytest.FixtureRequest, ignore_base) -> t.Tuple:
    if request.param is not object:
        yield request.param
    else:
        yield ((request.param,), {})


@pytest.fixture(params=super_classes_as_dataclass)
def base_super_class_as_dataclass(
    request: pytest.FixtureRequest, ignore_base
) -> t.Tuple:
    yield request.param


@pytest.fixture()
def ignore_base():
    copy = __model_database_metadata__.copy()
    __model_database_metadata__.clear()

    yield

    __model_database_metadata__.update(copy)


@pytest.fixture()
def db_service(tmp_path) -> EllarSQLService:
    return EllarSQLService(
        databases={
            "default": {"url": "sqlite:///:memory:", "echo": True, "future": True}
        },
        root_path=str(tmp_path),
    )


@pytest.fixture()
def db_service_async(tmp_path) -> EllarSQLService:
    return EllarSQLService(
        databases={
            "default": {
                "url": "sqlite+aiosqlite:///:memory:",
                "echo": True,
                "future": True,
            }
        },
        root_path=str(tmp_path),
    )


@pytest.fixture()
def app_setup(tmp_path):
    def _setup(**kwargs):
        sql_module = kwargs.pop("sql_module", {})
        sql_module.setdefault(
            "databases",
            {
                "default": {
                    "url": "sqlite://",
                    "echo": True,
                    "future": True,
                }
            },
        )
        sql_module.setdefault("migration_options", {"directory": "migrations"})
        tm = Test.create_test_module(
            modules=[EllarSQLModule.setup(root_path=str(tmp_path), **sql_module)],
            **kwargs,
        )
        return tm.create_application()

    return _setup


@pytest.fixture()
def app_setup_async(tmp_path):
    def _setup(**kwargs):
        sql_module = kwargs.pop("sql_module", {})
        sql_module.setdefault(
            "databases",
            {
                "default": {
                    "url": "sqlite+aiosqlite://",
                    "echo": True,
                    "future": True,
                }
            },
        )
        sql_module.setdefault("migration_options", {"directory": "migrations"})
        tm = Test.create_test_module(
            modules=[EllarSQLModule.setup(root_path=str(tmp_path), **sql_module)],
            **kwargs,
        )
        return tm.create_application()

    return _setup


@pytest.fixture()
async def app_ctx(app_setup):
    app = app_setup()

    async with app.application_context():
        yield app


@pytest.fixture()
async def app_ctx_async(app_setup_async):
    app = app_setup_async()

    async with app.application_context():
        yield app
