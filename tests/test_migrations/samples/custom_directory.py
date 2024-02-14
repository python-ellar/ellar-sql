#!/bin/env python

import click
from ellar.app import AppFactory, current_injector
from ellar.utils.importer import get_main_directory_by_stack
from ellar_cli.main import create_ellar_cli
from models import User

from ellar_sql import EllarSQLModule, MigrationOption, model


def bootstrap():
    path = get_main_directory_by_stack(
        "__main__/__parent__/__parent__/dumbs/custom_directory", stack_level=1
    )
    application = AppFactory.create_app(
        modules=[
            EllarSQLModule.setup(
                databases="sqlite:///app.db",
                migration_options=MigrationOption(
                    directory="temp_migrations",
                    context_configure={"compare_types": True},
                ),
                root_path=str(path),
            )
        ]
    )
    return application


cli = create_ellar_cli("custom_directory:bootstrap")


@cli.command()
def add_user():
    session = current_injector.get(model.Session)
    user = User(name="Custom Directory App Ellar")
    session.add(user)

    session.commit()

    click.echo(f"<User name={user.name} id={user.id}>")


if __name__ == "__main__":
    cli()
