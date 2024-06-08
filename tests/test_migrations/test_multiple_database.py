from ..utils import clean_directory, run_command, set_env_variable


@clean_directory("multiple")
def test_migrate_upgrade_for_multiple_database():
    with set_env_variable("multiple_db", "true"):
        result = run_command("multiple_database.py db init -m")
        assert result.returncode == 0
        assert (
            b"tests/dumbs/multiple/migrations/alembic.ini' before proceeding."
            in result.stdout
        )

        result = run_command("multiple_database.py db check")
        assert result.returncode == 1

        result = run_command("multiple_database.py db migrate")
        assert result.returncode == 0

        result = run_command("multiple_database.py db check")
        assert result.returncode == 1

        result = run_command("multiple_database.py db upgrade")
        assert result.returncode == 0

        result = run_command("multiple_database.py db check")
        assert result.returncode == 0
        assert result.stdout == b"No new upgrade operations detected.\n"

        result = run_command("multiple_database.py add-user")
        assert result.returncode == 0
        assert (
            result.stdout
            == b"<User name=Multiple Database App Ellar id=1 and Group name=group id=1>\n"
        )


@clean_directory("multiple")
def test_migrate_upgrade_multiple_database_with_model_changes():
    with set_env_variable("multiple_db", "true"):
        result = run_command("multiple_database.py db init -m")
        assert result.returncode == 0

        result = run_command("multiple_database.py db migrate")
        assert result.returncode == 0

        result = run_command("multiple_database.py db upgrade")
        assert result.returncode == 0

        with set_env_variable("model_change_name", "true"):
            result = run_command("multiple_database.py db migrate")
            assert result.returncode == 0
            assert (
                b"Detected type change from VARCHAR(length=256) to String(length=128)"
                in result.stderr
            )


@clean_directory("multiple_async")
def test_migrate_upgrade_for_multiple_database_async():
    with set_env_variable("multiple_db", "true"):
        result = run_command("multiple_database_async.py db init -m")
        assert result.returncode == 0
        assert (
            b"tests/dumbs/multiple_async/migrations/alembic.ini' before proceeding."
            in result.stdout
        )

        result = run_command("multiple_database_async.py db check")
        assert result.returncode == 1

        result = run_command("multiple_database_async.py db migrate")
        assert result.returncode == 0

        result = run_command("multiple_database_async.py db check")
        assert result.returncode == 1

        result = run_command("multiple_database_async.py db upgrade")
        assert result.returncode == 0

        result = run_command("multiple_database_async.py db check")
        assert result.returncode == 0
        assert result.stdout == b"No new upgrade operations detected.\n"

        result = run_command("multiple_database_async.py add-user")
        assert result.returncode == 0
        assert (
            result.stdout
            == b"<User name=Multiple Database App Ellar id=1 and Group name=group id=1>\n"
        )
