import ellar_cli.click as click
from ellar.app import current_injector

from ellar_sql.services import EllarSQLService

from .handlers import CLICommandHandlers


def _get_handler_context(ctx: click.Context) -> CLICommandHandlers:
    db_service = current_injector.get(EllarSQLService)
    return CLICommandHandlers(db_service)


@click.group()
def db():
    """- Perform Alembic Database Commands -"""
    pass


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option("-m", "--message", default=None, help="Revision message")
@click.option(
    "--autogenerate",
    is_flag=True,
    help=(
        "Populate revision script with candidate migration "
        "operations, based on comparison of database to model"
    ),
)
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output " "instead",
)
@click.option(
    "--head",
    default="head",
    help="Specify head revision or <branchname>@head to base new " "revision on",
)
@click.option(
    "--splice",
    is_flag=True,
    help='Allow a non-head revision as the "head" to splice onto',
)
@click.option(
    "--branch-label",
    default=None,
    help="Specify a branch label to apply to the new revision",
)
@click.option(
    "--version-path",
    default=None,
    help="Specify specific path from config for version file",
)
@click.option(
    "--rev-id",
    default=None,
    help="Specify a hardcoded revision id instead of generating " "one",
)
@click.pass_context
def revision(
    ctx,
    directory,
    message,
    autogenerate,
    sql,
    head,
    splice,
    branch_label,
    version_path,
    rev_id,
):
    """- Create a new revision file."""
    handler = _get_handler_context(ctx)
    handler.revision(
        directory,
        message,
        autogenerate,
        sql,
        head,
        splice,
        branch_label,
        version_path,
        rev_id,
    )


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option("-m", "--message", default=None, help="Revision message")
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output " "instead",
)
@click.option(
    "--head",
    default="head",
    help="Specify head revision or <branchname>@head to base new " "revision on",
)
@click.option(
    "--splice",
    is_flag=True,
    help='Allow a non-head revision as the "head" to splice onto',
)
@click.option(
    "--branch-label",
    default=None,
    help="Specify a branch label to apply to the new revision",
)
@click.option(
    "--version-path",
    default=None,
    help="Specify specific path from config for version file",
)
@click.option(
    "--rev-id",
    default=None,
    help="Specify a hardcoded revision id instead of generating " "one",
)
@click.option(
    "-x",
    "--x-arg",
    multiple=True,
    help="Additional arguments consumed by custom env.py scripts",
)
@click.pass_context
def migrate(
    ctx,
    directory,
    message,
    sql,
    head,
    splice,
    branch_label,
    version_path,
    rev_id,
    x_arg,
):
    """- Autogenerate a new revision file (Alias for
    'revision --autogenerate')"""
    handler = _get_handler_context(ctx)
    handler.migrate(
        directory,
        message,
        sql,
        head,
        splice,
        branch_label,
        version_path,
        rev_id,
        x_arg,
    )


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.argument("revision", default="head")
@click.pass_context
def edit(ctx, directory, revision):
    """- Edit a revision file"""
    handler = _get_handler_context(ctx)
    handler.edit(directory, revision)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option("-m", "--message", default=None, help="Merge revision message")
@click.option(
    "--branch-label",
    default=None,
    help="Specify a branch label to apply to the new revision",
)
@click.option(
    "--rev-id",
    default=None,
    help="Specify a hardcoded revision id instead of generating " "one",
)
@click.argument("revisions", nargs=-1)
@click.pass_context
def merge(ctx, directory, message, branch_label, rev_id, revisions):
    """- Merge two revisions together, creating a new revision file"""
    handler = _get_handler_context(ctx)
    handler.merge(directory, revisions, message, branch_label, rev_id)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output " "instead",
)
@click.option(
    "--tag",
    default=None,
    help='Arbitrary "tag" name - can be used by custom env.py ' "scripts",
)
@click.option(
    "-x",
    "--x-arg",
    multiple=True,
    help="Additional arguments consumed by custom env.py scripts",
)
@click.argument("revision", default="head")
@click.pass_context
def upgrade(ctx, directory, sql, tag, x_arg, revision):
    """- Upgrade to a later version"""
    handler = _get_handler_context(ctx)
    handler.upgrade(directory, revision, sql, tag, x_arg)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output " "instead",
)
@click.option(
    "--tag",
    default=None,
    help='Arbitrary "tag" name - can be used by custom env.py ' "scripts",
)
@click.option(
    "-x",
    "--x-arg",
    multiple=True,
    help="Additional arguments consumed by custom env.py scripts",
)
@click.argument("revision", default="-1")
@click.pass_context
def downgrade(ctx: click.Context, directory, sql, tag, x_arg, revision):
    """- Revert to a previous version"""
    handler = _get_handler_context(ctx)
    handler.downgrade(directory, revision, sql, tag, x_arg)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.argument("revision", default="head")
@click.pass_context
def show(ctx: click.Context, directory, revision):
    """- Show the revision denoted by the given symbol."""
    handler = _get_handler_context(ctx)
    handler.show(directory, revision)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option(
    "-r",
    "--rev-range",
    default=None,
    help="Specify a revision range; format is [start]:[end]",
)
@click.option("-v", "--verbose", is_flag=True, help="Use more verbose output")
@click.option(
    "-i",
    "--indicate-current",
    is_flag=True,
    help="Indicate current version (Alembic 0.9.9 or greater is " "required)",
)
@click.pass_context
def history(ctx: click.Context, directory, rev_range, verbose, indicate_current):
    """- List changeset scripts in chronological order."""
    handler = _get_handler_context(ctx)
    handler.history(directory, rev_range, verbose, indicate_current)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option("-v", "--verbose", is_flag=True, help="Use more verbose output")
@click.option(
    "--resolve-dependencies",
    is_flag=True,
    help="Treat dependency versions as down revisions",
)
@click.pass_context
def heads(ctx: click.Context, directory, verbose, resolve_dependencies):
    """- Show current available heads in the script directory"""
    handler = _get_handler_context(ctx)
    handler.heads(directory, verbose, resolve_dependencies)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option("-v", "--verbose", is_flag=True, help="Use more verbose output")
@click.pass_context
def branches(ctx, directory, verbose):
    """- Show current branch points"""
    handler = _get_handler_context(ctx)
    handler.branches(directory, verbose)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option("-v", "--verbose", is_flag=True, help="Use more verbose output")
@click.pass_context
def current(ctx: click.Context, directory, verbose):
    """- Display the current revision for each database."""
    handler = _get_handler_context(ctx)
    handler.current(directory, verbose)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output " "instead",
)
@click.option(
    "--tag",
    default=None,
    help='Arbitrary "tag" name - can be used by custom env.py ' "scripts",
)
@click.argument("revision", default="head")
@click.pass_context
def stamp(ctx: click.Context, directory, sql, tag, revision):
    """- 'stamp' the revision table with the given revision; don't run any
    migrations"""
    handler = _get_handler_context(ctx)
    handler.stamp(directory, revision, sql, tag)


@db.command()
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.pass_context
def check(ctx: click.Context, directory):
    """Check if there are any new operations to migrate"""
    handler = _get_handler_context(ctx)
    handler.check(directory)


@db.command("init")
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option(
    "-m",
    "--multiple",
    default=False,
    is_flag=True,
    help='Use multiple migration template (default is "False")',
)
@click.option(
    "--package",
    is_flag=True,
    help="Write empty __init__.py files to the environment and " "version locations",
)
@click.pass_context
def init(ctx: click.Context, directory, multiple, package):
    """Creates a new migration repository."""
    handler = _get_handler_context(ctx)
    handler.alembic_init(directory, multiple, package)
