#!/bin/env python
import click
from ellar.app import AppFactory, current_injector
from ellar.common.utils.importer import get_main_directory_by_stack
from ellar_cli.main import create_ellar_cli
from models import User

from ellar_sqlalchemy import EllarSQLAlchemyModule, model


def bootstrap():
    path = get_main_directory_by_stack(
        "__main__/__parent__/__parent__/dumbs/default", stack_level=1
    )
    application = AppFactory.create_app(
        modules=[
            EllarSQLAlchemyModule.setup(
                databases="sqlite:///app.db",
                migration_options={"context_configure": {"compare_types": False}},
                root_path=str(path),
            )
        ]
    )
    return application


cli = create_ellar_cli("default:bootstrap")


@cli.command()
def add_user():
    session = current_injector.get(model.Session)
    user = User(name="default App Ellar")
    session.add(user)

    session.commit()
    click.echo(f"<User name={user.name} id={user.id}>")


if __name__ == "__main__":
    cli()
