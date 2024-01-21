from ellar_sql import model
from ellar_sql.model.database_binds import get_metadata


def test_bind_key_default(ignore_base):
    user_table = model.Table(
        "user", model.Column("id", model.Integer, primary_key=True)
    )
    default_metadata = get_metadata("default")
    assert user_table.metadata is default_metadata


def test_metadata_per_bind(ignore_base):
    user_table = model.Table(
        "user",
        model.Column("id", model.Integer, primary_key=True),
        __database__="other",
    )
    other_metadata = get_metadata("other")
    assert user_table.metadata is other_metadata


def test_multiple_binds_same_table_name(ignore_base):
    user1_table = model.Table(
        "user", model.Column("id", model.Integer, primary_key=True)
    )
    user2_table = model.Table(
        "user",
        model.Column("id", model.Integer, primary_key=True),
        __database__="other",
    )
    other_metadata = get_metadata("other")
    default_metadata = get_metadata("default")
    assert user1_table.metadata is default_metadata
    assert user2_table.metadata is other_metadata


def test_explicit_metadata(ignore_base):
    other_metadata = model.MetaData()
    user_table = model.Table(
        "user",
        other_metadata,
        model.Column("id", model.Integer, primary_key=True),
        __database__="other",
    )
    assert user_table.metadata is other_metadata
    other_metadata = get_metadata("other")
    assert other_metadata is None
