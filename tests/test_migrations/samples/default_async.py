#!/bin/env python
import ellar_cli.click as click
from ellar.app import AppFactory, current_injector
from ellar.common.utils.importer import get_main_directory_by_stack
from ellar_cli.main import create_ellar_cli
from models import User
from sqlalchemy.ext.asyncio import AsyncSession

from ellar_sql import EllarSQLModule


def bootstrap():
    path = get_main_directory_by_stack(
        "__main__/__parent__/__parent__/dumbs/default_async", stack_level=1
    )
    application = AppFactory.create_app(
        modules=[
            EllarSQLModule.setup(
                databases="sqlite+aiosqlite:///app.db",
                migration_options={"context_configure": {"compare_types": False}},
                root_path=str(path),
            )
        ]
    )
    return application


cli = create_ellar_cli("default_async:bootstrap")


@cli.command()
@click.run_as_async
async def add_user():
    session = current_injector.get(AsyncSession)
    user = User(name="default App Ellar")
    session.add(user)

    await session.commit()
    await session.refresh(user)
    await session.close()

    click.echo(f"<User name={user.name} id={user.id}>")


if __name__ == "__main__":
    cli()
