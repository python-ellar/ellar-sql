#!/bin/env python
import click
from ellar.app import AppFactory, current_injector
from ellar.utils.importer import get_main_directory_by_stack
from ellar_cli.main import create_ellar_cli
from models import Group, User

from ellar_sql import EllarSQLModule, model


def bootstrap():
    path = get_main_directory_by_stack(
        "__main__/__parent__/__parent__/dumbs/multiple", stack_level=1
    )
    application = AppFactory.create_app(
        modules=[
            EllarSQLModule.setup(
                databases={
                    "default": "sqlite:///app.db",
                    "db1": "sqlite:///app2.db",
                },
                migration_options={"context_configure": {"compare_types": False}},
                root_path=str(path),
            )
        ]
    )
    return application


cli = create_ellar_cli("multiple_database:bootstrap")


@cli.command()
def add_user():
    session = current_injector.get(model.Session)
    user = User(name="Multiple Database App Ellar")
    group = Group(name="group")
    session.add(user)
    session.add(group)

    session.commit()

    click.echo(
        f"<User name={user.name} id={user.id} and Group name={group.name} id={group.id}>"
    )


if __name__ == "__main__":
    cli()
