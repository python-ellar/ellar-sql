#!/bin/env python
import ellar_cli.click as click
from ellar.app import AppFactory, current_injector
from ellar.common.utils.importer import get_main_directory_by_stack
from ellar_cli.main import create_ellar_cli
from models import Group, User
from sqlalchemy.ext.asyncio import AsyncSession

from ellar_sql import EllarSQLModule


def bootstrap():
    path = get_main_directory_by_stack(
        "__main__/__parent__/__parent__/dumbs/multiple_async", stack_level=1
    )
    application = AppFactory.create_app(
        modules=[
            EllarSQLModule.setup(
                databases={
                    "default": "sqlite+aiosqlite:///app.db",
                    "db1": "sqlite+aiosqlite:///app2.db",
                },
                migration_options={"context_configure": {"compare_types": False}},
                root_path=str(path),
            )
        ]
    )
    return application


cli = create_ellar_cli("multiple_database_async:bootstrap")


@cli.command()
@click.run_as_async
async def add_user():
    session = current_injector.get(AsyncSession)
    user = User(name="Multiple Database App Ellar")
    group = Group(name="group")

    session.add(user)
    session.add(group)

    await session.commit()

    await session.refresh(user)
    await session.refresh(group)

    await session.close()

    click.echo(
        f"<User name={user.name} id={user.id} and Group name={group.name} id={group.id}>"
    )


if __name__ == "__main__":
    cli()
