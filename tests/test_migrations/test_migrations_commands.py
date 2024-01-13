from ..utils import clean_directory, run_command, set_env_variable


@clean_directory("default")
def test_migrate_upgrade():
    result = run_command("default.py db init")
    assert result.returncode == 0
    assert (
        b"tests/dumbs/default/migrations/alembic.ini' before proceeding."
        in result.stdout
    )

    result = run_command("default.py db check")
    assert result.returncode == 1

    result = run_command("default.py db migrate")
    assert result.returncode == 0

    result = run_command("default.py db check")
    assert result.returncode == 1

    result = run_command("default.py db upgrade")
    assert result.returncode == 0

    result = run_command("default.py db check")
    assert result.returncode == 0
    assert result.stdout == b"No new upgrade operations detected.\n"

    result = run_command("default.py add-user")
    assert result.returncode == 0
    assert result.stdout == b"<User name=default App Ellar id=1>\n"


@clean_directory("custom_directory")
def test_migrate_upgrade_custom_directory():
    result = run_command("custom_directory.py db init")
    assert result.returncode == 0
    assert (
        b"tests/dumbs/custom_directory/temp_migrations/alembic.ini' before proceeding."
        in result.stdout
    )

    result = run_command("custom_directory.py db check")
    assert result.returncode == 1

    result = run_command("custom_directory.py db migrate")
    assert result.returncode == 0

    result = run_command("custom_directory.py db check")
    assert result.returncode == 1

    result = run_command("custom_directory.py db upgrade")
    assert result.returncode == 0

    result = run_command("custom_directory.py db check")
    assert result.returncode == 0
    assert result.stdout == b"No new upgrade operations detected.\n"

    result = run_command("custom_directory.py add-user")
    assert result.returncode == 0
    assert result.stdout == b"<User name=Custom Directory App Ellar id=1>\n"


@clean_directory("custom_directory")
def test_migrate_upgrade_custom_directory_with_model_changes():
    result = run_command("custom_directory.py db init")
    assert result.returncode == 0

    result = run_command("custom_directory.py db migrate")
    assert result.returncode == 0

    result = run_command("custom_directory.py db upgrade")
    assert result.returncode == 0

    with set_env_variable("model_change_name", "true"):
        result = run_command("custom_directory.py db migrate")
        assert result.returncode == 0
        assert (
            b"Detected type change from VARCHAR(length=256) to String(length=128)"
            in result.stderr
        )


@clean_directory("default")
def test_other_alembic_commands():
    result = run_command("default.py db init")
    assert result.returncode == 0

    # Revision Command
    result = run_command("default.py db revision")
    assert result.returncode == 0

    # Edit Command
    result = run_command("default.py db edit")
    assert result.returncode == 1
    assert b"TERM environment variable not set." in result.stderr

    # Merge Command
    result = run_command("default.py db merge")
    assert result.returncode == 2
    assert b"Missing argument '<revisions>, ..." in result.stderr

    # Show Command
    result = run_command("default.py db show")
    assert result.returncode == 0

    # History Command
    result = run_command("default.py db history")
    assert result.returncode == 0

    # Heads Command
    result = run_command("default.py db heads")
    assert result.returncode == 0

    # Branches Command
    result = run_command("default.py db branches")
    assert result.returncode == 0

    # Current Command
    result = run_command("default.py db current")
    assert result.returncode == 0

    # Stamp Command
    result = run_command("default.py db stamp")
    assert result.returncode == 1
    assert (
        b"revision identifier False is not a string; ensure database driver settings are correct"
        in result.stderr
    )

    # Downgrade Command
    result = run_command("default.py db downgrade")
    assert result.returncode == 1
    assert b"Relative revision -1 didn't produce 1 migrations" in result.stderr
