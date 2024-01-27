from __future__ import annotations

import argparse
import os
import typing as t
from functools import wraps
from pathlib import Path

import click
from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.util.exc import CommandError
from ellar.app import App

from ellar_sql.services import EllarSQLService

RevIdType = t.Union[str, t.List[str], t.Tuple[str, ...]]


class Config(AlembicConfig):
    def get_template_directory(self) -> str:
        package_dir = os.path.abspath(Path(__file__).parent.parent)
        return os.path.join(package_dir, "templates")


def _catch_errors(f: t.Callable) -> t.Callable:  # type:ignore[type-arg]
    @wraps(f)
    def wrapped(*args: t.Any, **kwargs: t.Any) -> None:
        try:
            f(*args, **kwargs)
        except (CommandError, RuntimeError) as exc:
            raise click.ClickException(str(exc)) from exc

    return wrapped


class CLICommandHandlers:
    def __init__(self, db_service: EllarSQLService) -> None:
        self.db_service = db_service

    def get_config(
        self,
        directory: t.Optional[t.Any] = None,
        x_arg: t.Optional[t.Any] = None,
        opts: t.Optional[t.Any] = None,
    ) -> Config:
        directory = (
            str(directory) if directory else self.db_service.migration_options.directory
        )

        config = Config(os.path.join(directory, "alembic.ini"))

        config.set_main_option("script_location", directory)
        config.set_main_option(
            "sqlalchemy.url", str(self.db_service.engine.url).replace("%", "%%")
        )

        if config.cmd_opts is None:
            config.cmd_opts = argparse.Namespace()

        for opt in opts or []:
            setattr(config.cmd_opts, opt, True)

        if not hasattr(config.cmd_opts, "x"):
            if x_arg is not None:
                config.cmd_opts.x = []

                if isinstance(x_arg, list) or isinstance(x_arg, tuple):
                    for x in x_arg:
                        config.cmd_opts.x.append(x)
                else:
                    config.cmd_opts.x.append(x_arg)
            else:
                config.cmd_opts.x = None
        return config

    @_catch_errors
    def alembic_init(
        self,
        directory: str | None = None,
        multiple: bool = False,
        package: bool = False,
    ) -> None:
        """Creates a new migration repository"""
        if directory is None:
            directory = self.db_service.migration_options.directory

        config = Config()
        config.set_main_option("script_location", directory)
        config.config_file_name = os.path.join(directory, "alembic.ini")

        template_name = "single"

        if multiple:
            template_name = "multiple"

        command.init(config, directory, template=template_name, package=package)

    @_catch_errors
    def revision(
        self,
        directory: str | None = None,
        message: str | None = None,
        autogenerate: bool = False,
        sql: bool = False,
        head: str = "head",
        splice: bool = False,
        branch_label: RevIdType | None = None,
        version_path: str | None = None,
        rev_id: str | None = None,
    ) -> None:
        """Create a new revision file."""
        opts = ["autogenerate"] if autogenerate else None

        config = self.get_config(directory, opts=opts)
        command.revision(
            config,
            message,
            autogenerate=autogenerate,
            sql=sql,
            head=head,
            splice=splice,
            branch_label=branch_label,
            version_path=version_path,
            rev_id=rev_id,
        )

    @_catch_errors
    def migrate(
        self,
        directory: str | None = None,
        message: str | None = None,
        sql: bool = False,
        head: str = "head",
        splice: bool = False,
        branch_label: RevIdType | None = None,
        version_path: str | None = None,
        rev_id: str | None = None,
        x_arg: str | None = None,
    ) -> None:
        """Alias for 'revision --autogenerate'"""
        config = self.get_config(
            directory,
            opts=["autogenerate"],
            x_arg=x_arg,
        )
        command.revision(
            config,
            message,
            autogenerate=True,
            sql=sql,
            head=head,
            splice=splice,
            branch_label=branch_label,
            version_path=version_path,
            rev_id=rev_id,
        )

    @_catch_errors
    def edit(self, directory: str | None = None, revision: str = "current") -> None:
        """Edit current revision."""
        config = self.get_config(directory)
        command.edit(config, revision)

    @_catch_errors
    def merge(
        self,
        directory: str | None = None,
        revisions: RevIdType = "",
        message: str | None = None,
        branch_label: RevIdType | None = None,
        rev_id: str | None = None,
    ) -> None:
        """Merge two revisions together.  Creates a new migration file"""
        config = self.get_config(directory)
        command.merge(
            config, revisions, message=message, branch_label=branch_label, rev_id=rev_id
        )

    @_catch_errors
    def upgrade(
        self,
        directory: str | None = None,
        revision: str = "head",
        sql: bool = False,
        tag: str | None = None,
        x_arg: str | None = None,
    ) -> None:
        """Upgrade to a later version"""
        config = self.get_config(directory, x_arg=x_arg)
        command.upgrade(config, revision, sql=sql, tag=tag)

    @_catch_errors
    def downgrade(
        self,
        directory: str | None = None,
        revision: str = "-1",
        sql: bool = False,
        tag: str | None = None,
        x_arg: str | None = None,
    ) -> None:
        """Revert to a previous version"""
        config = self.get_config(directory, x_arg=x_arg)
        if sql and revision == "-1":
            revision = "head:-1"
        command.downgrade(config, revision, sql=sql, tag=tag)

    @_catch_errors
    def show(self, directory: str | None = None, revision: str = "head") -> None:
        """Show the revision denoted by the given symbol."""
        config = self.get_config(directory)
        command.show(config, revision)  # type:ignore[no-untyped-call]

    @_catch_errors
    def history(
        self,
        directory: str | None = None,
        rev_range: t.Any = None,
        verbose: bool = False,
        indicate_current: bool = False,
    ) -> None:
        """List changeset scripts in chronological order."""
        config = self.get_config(directory)
        command.history(
            config, rev_range, verbose=verbose, indicate_current=indicate_current
        )

    @_catch_errors
    def heads(
        self,
        directory: str | None = None,
        verbose: bool = False,
        resolve_dependencies: bool = False,
    ) -> None:
        """Show current available heads in the script directory"""
        config = self.get_config(directory)
        command.heads(  # type:ignore[no-untyped-call]
            config, verbose=verbose, resolve_dependencies=resolve_dependencies
        )

    @_catch_errors
    def branches(self, directory: str | None = None, verbose: bool = False) -> None:
        """Show current branch points"""
        config = self.get_config(directory)
        command.branches(config, verbose=verbose)  # type:ignore[no-untyped-call]

    @_catch_errors
    def current(self, directory: str | None = None, verbose: bool = False) -> None:
        """Display the current revision for each database."""
        config = self.get_config(directory)
        command.current(config, verbose=verbose)

    @_catch_errors
    def stamp(
        self,
        app: App,
        directory: str | None = None,
        revision: str = "head",
        sql: bool = False,
        tag: t.Any = None,
    ) -> None:
        """'stamp' the revision table with the given revision; don't run any
        migrations"""
        config = self.get_config(app, directory)
        command.stamp(config, revision, sql=sql, tag=tag)

    @_catch_errors
    def check(self, app: App, directory: str | None = None) -> None:
        """Check if there are any new operations to migrate"""
        config = self.get_config(app, directory)
        command.check(config)
