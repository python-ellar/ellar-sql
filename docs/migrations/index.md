# **Migrations**
EllarSQL also extends **Alembic** package
to add migration functionality and make database operations accessible through **EllarCLI** commandline interface.

**EllarSQL** with Alembic does not override Alembic action rather provide Alembic all the configs/information
it needs to for a proper migration/database operations.
Its also still possible to use Alembic outside EllarSQL setup when necessary.

This section is inspired by [`Flask Migrate`](https://flask-migrate.readthedocs.io/en/latest/#)

## **Quick Example**
We assume you have set up `EllarSQLModule` in your application, and you have specified `migration_options`.

Create a simple `User` model as shown below:

```python
from ellar_sql import model


class User(model.Model):
    id = model.Column(model.Integer, primary_key=True)
    name = model.Column(model.String(128))
```

### **Initialize migration template**
With the Model setup, run the command below

```shell
# Initialize the database
ellar db init
```

Executing this command will incorporate a migrations folder into your application structure. 
Ensure that the contents of this folder are included in version control alongside your other source files.

Following the initialization, you can generate an initial migration using the command:

```shell
# Generate the initial migration
ellar db migrate -m "Initial migration."
```
Few things to do after generating a migration file:

- Review and edit the migration script
- Alembic may not detect certain changes automatically, such as table and column name modifications or unnamed constraints. Refer to the [Alembic autogenerate documentation](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect) for a comprehensive list of limitations.
- Add the finalized migration script to version control
- Ensure that the edited script is committed along with your source code changes

Apply the changes described in the migration script to your database

```shell
ellar db upgrade
```

Whenever there are changes to the database models, it's necessary to repeat the `migrate` and `upgrade` commands.

For synchronizing the database on another system, simply refresh the migrations folder from the source control repository 
and execute the `upgrade` command. This ensures that the database structure aligns with the latest changes in the models.

### **Multiple Database Migration**
If your application utilizes multiple databases, a distinct Alembic template for migration is required. 
To enable this, include `-m` or `--multi` with the `db init` command, as demonstrated below:

```shell
ellar db init --multi
```

## **Command Reference**
All Alembic commands are expose to Ellar CLI under `db` group after a successful `EllarSQLModule` setup.

To see all the commands that are available run this command:
```shell
ellar db --help

# output
Usage: ellar db [OPTIONS] COMMAND [ARGS]...

  - Perform Alembic Database Commands -

Options:
  --help  Show this message and exit.

Commands:
  branches   - Show current branch points
  check      Check if there are any new operations to migrate
  current    - Display the current revision for each database.
  downgrade  - Revert to a previous version
  edit       - Edit a revision file
  heads      - Show current available heads in the script directory
  history    - List changeset scripts in chronological order.
  init       Creates a new migration repository.
  merge      - Merge two revisions together, creating a new revision file
  migrate    - Autogenerate a new revision file (Alias for 'revision...
  revision   - Create a new revision file.
  show       - Show the revision denoted by the given symbol.
  stamp      - 'stamp' the revision table with the given revision; don't...
  upgrade    - Upgrade to a later version

```

- `ellar db --help` 
  Shows a list of available commands.


- `ellar db revision [--message MESSAGE] [--autogenerate] [--sql] [--head HEAD] [--splice] [--branch-label BRANCH_LABEL] [--version-path VERSION_PATH] [--rev-id REV_ID]`
  Creates an empty revision script. The script needs to be edited manually with the upgrade and downgrade changes. See Alembic’s documentation for instructions on how to write migration scripts. An optional migration message can be included.


- `ellar db migrate [--message MESSAGE] [--sql] [--head HEAD] [--splice] [--branch-label BRANCH_LABEL] [--version-path VERSION_PATH] [--rev-id REV_ID]`
  Equivalent to revision --autogenerate. The migration script is populated with changes detected automatically. The generated script should be reviewed and edited as not all types of changes can be detected automatically. This command does not make any changes to the database, just creates the revision script.


- `ellar db check`
  Checks that a migrate command would not generate any changes. If pending changes are detected, the command exits with a non-zero status code.


- `ellar db edit <revision>`
  Edit a revision script using $EDITOR.


- `ellar db upgrade [--sql] [--tag TAG] <revision>`
  Upgrades the database. If revision isn’t given, then "head" is assumed.


- `ellar db downgrade [--sql] [--tag TAG] <revision>`
  Downgrades the database. If revision isn’t given, then -1 is assumed.


- `ellar db stamp [--sql] [--tag TAG] <revision>`
  Sets the revision in the database to the one given as an argument, without performing any migrations.


- `ellar db current [--verbose]`
  Shows the current revision of the database.


- `ellar db history [--rev-range REV_RANGE] [--verbose]`
  Shows the list of migrations. If a range isn’t given, then the entire history is shown.


- `ellar db show <revision>`
  Show the revision denoted by the given symbol.


- `ellar db merge [--message MESSAGE] [--branch-label BRANCH_LABEL] [--rev-id REV_ID] <revisions>`
  Merge two revisions together. Create a new revision file.


- `ellar db heads [--verbose] [--resolve-dependencies]`
  Show current available heads in the revision script directory.


- `ellar db branches [--verbose]`
  Show current branch points.
