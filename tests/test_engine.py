import os.path
import unittest.mock

import pytest
from ellar.common.exceptions import ImproperConfiguration

from ellar_sqlalchemy import EllarSQLAlchemyService, model


def test_engine_per_bind(tmp_path, ignore_base):
    db_service = EllarSQLAlchemyService(
        databases={"default": "sqlite://", "a": "sqlite://"},
        root_path=str(tmp_path),
    )
    assert db_service.engines["a"] is not db_service.engine


def test_config_engine_options(ignore_base):
    db_service = EllarSQLAlchemyService(
        databases={"default": "sqlite://", "a": "sqlite://"},
        common_engine_options={"echo": True},
    )
    assert db_service.engine.echo
    assert db_service.engines["a"].echo


def test_init_engine_options(ignore_base):
    db_service = EllarSQLAlchemyService(
        databases={"default": "sqlite://", "a": {"url": "sqlite://", "echo": True}},
        common_engine_options={"echo": False},
    )
    assert not db_service.engine.echo
    assert db_service.engines["a"].echo


def test_config_echo(ignore_base):
    db_service = EllarSQLAlchemyService(databases={"default": "sqlite://"}, echo=True)
    assert db_service.engine.echo
    assert db_service.engine.pool.echo


@pytest.mark.parametrize(
    "value",
    [
        "sqlite://",
        model.engine.URL.create("sqlite"),
        {"url": "sqlite://"},
        {"url": model.engine.URL.create("sqlite")},
    ],
)
def test_url_type(value, ignore_base):
    db_service = EllarSQLAlchemyService(
        databases={"default": "sqlite://", "a": value}, echo=True
    )
    assert str(db_service.engines["a"].url) == "sqlite://"


def test_no_default_database_error(ignore_base):
    with pytest.raises(ImproperConfiguration) as info:
        EllarSQLAlchemyService(
            databases={},
        )
    e = "`default` database must be present in databases parameter: {}"
    assert str(info.value) == e


def test_sqlite_relative_path(ignore_base, tmp_path):
    db_service = EllarSQLAlchemyService(
        databases={"default": "sqlite:///test.db"}, root_path=str(tmp_path)
    )
    db_service.create_all()
    assert not isinstance(db_service.engine.pool, model.pool.StaticPool)
    db_path = db_service.engine.url.database
    assert db_path.startswith(str(tmp_path))
    assert os.path.exists(db_path)


def test_sqlite_driver_level_uri(tmp_path, ignore_base):
    db_service = EllarSQLAlchemyService(
        databases={"default": "sqlite:///file:test.db?uri=true"},
        root_path=str(tmp_path),
    )
    db_service.create_all()
    db_path = db_service.engine.url.database
    assert db_path is not None
    assert db_path.startswith(f"file:{tmp_path}")
    assert os.path.exists(db_path[5:])


@unittest.mock.patch.object(EllarSQLAlchemyService, "_make_engine", autospec=True)
def test_sqlite_memory_defaults(
    make_engine: unittest.mock.Mock, tmp_path, ignore_base
) -> None:
    EllarSQLAlchemyService(databases={"default": "sqlite://"}, root_path=str(tmp_path))
    options = make_engine.call_args[0][1]
    assert options["poolclass"] is model.pool.StaticPool
    assert options["connect_args"]["check_same_thread"] is False


@unittest.mock.patch.object(EllarSQLAlchemyService, "_make_engine", autospec=True)
def test_mysql_defaults(make_engine: unittest.mock.Mock, tmp_path, ignore_base) -> None:
    EllarSQLAlchemyService(
        databases={"default": "mysql:///test"}, root_path=str(tmp_path)
    )
    options = make_engine.call_args[0][1]
    assert options["pool_recycle"] == 7200
    assert options["url"].query["charset"] == "utf8mb4"
