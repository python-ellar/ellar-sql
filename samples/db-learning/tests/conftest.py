import os

import pytest
from db_learning.root_module import ApplicationModule
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.testing import Test
from ellar.threading.sync_worker import execute_async_context_manager

from ellar_sql import EllarSQLService

os.environ.setdefault(ELLAR_CONFIG_MODULE, "db_learning.config:TestConfig")


@pytest.fixture(scope="session")
def tm():
    test_module = Test.create_test_module(modules=[ApplicationModule])
    app = test_module.create_application()

    with execute_async_context_manager(app.with_injector_context()):
        yield test_module


@pytest.fixture(scope="session")
def db(tm):
    db_service = tm.get(EllarSQLService)
    db_service.create_all()

    yield

    db_service.session_factory.remove()
    db_service.drop_all()
