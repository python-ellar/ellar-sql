# **EllarSQLModule Config**
**`EllarSQLModule`** is an Ellar Dynamic Module that offers two ways of configuration:

- `EllarSQLModule.register_setup()`: This method registers a `ModuleSetup` that depends on the application config.
- `EllarSQLModule.setup()`: This method immediately sets up the module with the provided options.

While we've explored many examples using `EllarSQLModule.setup()`, this section will focus on the usage of `EllarSQLModule.register_setup()`.

Before delving into that, let's first explore the setup options available for `EllarSQLModule`.
## **EllarSQLModule Configuration Parameters**

- **databases**: _typing.Union[str, typing.Dict[str, typing.Any]]_:
    
    This field describes the options for your database engine, utilized by SQLAlchemy **Engine**, **Metadata**, and **Sessions**. There are three methods for setting these options, as illustrated below:
    ```python
    ## CASE 1
    databases = "sqlite//:memory:"
    # This will result to 
    # databases = {
    #     'default': {
    #         'url': 'sqlite//:memory:'
    #     }
    # }
    
    ## CASE 2
    databases = {
        'default': "sqlite//:memory:",
        'db2': "sqlite//:memory:",
    }
    # This will result to 
    # databases = {
    #     'default': {
    #         'url': 'sqlite//:memory:'
    #     },
    #     'db2': {
    #         'url': 'sqlite//:memory:'
    #     },
    # }
    
    ## CASE 3 - With Extra Engine Options
    databases = {
        'default': {
            "url": "sqlite//:memory:",
            "echo": True,
            "connect_args": {
                "check_same_thread": False
            }
        }
    }
    ```


- **migration_options**: _typing.Union[typing.Dict[str, typing.Any], MigrationOption]_:
  The migration options can be specified either in a dictionary object or as a `MigrationOption` schema instance. 
  These configurations are essential for defining the necessary settings for database migrations. The available options include:
    - **directory**=`migrations`:directory to save alembic migration templates/env and migration versions
    - **use_two_phase**=`True`: bool value that indicates use of two in migration SQLAlchemy session
    - **context_configure**=`{compare_type: True, render_as_batch: True, include_object: callable}`: 
        key-value pair that will be passed to [`EnvironmentContext.configure`](https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.environment.EnvironmentContext.configure){target="_blank"}.
  
        Default **context_configure** set by EllarSQL:
  
        - **compare_type=True**: This option configures the automatic migration generation subsystem to detect column type changes.
        - **render_as_batch=True**: This option generates migration scripts using [batch mode](https://alembic.sqlalchemy.org/en/latest/batch.html){target="_blank"}, an operational mode that works around limitations of many ALTER commands in the SQLite database by implementing a “move and copy” workflow.
        - **include_object**: Skips model from auto gen when it's defined in table args eg: `__table_args__ = {"info": {"skip_autogen": True}}`

- **session_options**: _t.Optional[t.Dict[str, t.Any]]_:

    A default key-value pair pass to [SQLAlchemy.Session()](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session){target="_blank"} when creating a session.

- **engine_options**: _t.Optional[t.Dict[str, t.Any]]_:

    A default key-value pair to pass to every database configuration engine configuration for [SQLAlchemy.create_engine()](https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine){target="_blank"}.
  
    This overriden by configurations provided in `databases` parameters

- **models**: _t.Optional[t.List[str]]_: list of python modules that defines `model.Model` models. By providing this, EllarSQL ensures models are discovered before Alembic CLI migration actions or any other database interactions with SQLAlchemy.

- **echo**: _bool_: The default value for `echo` and `echo_pool` for every engine. This is useful to quickly debug the connections and queries issued from SQLAlchemy.

- **root_path**: _t.Optional[str]_: The `root_path` for sqlite databases and migration base directory. Defaults to the execution path of `EllarSQLModule` 

## **Connection URL Format**
Refer to SQLAlchemy’s documentation on [Engine Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html){target="_blank"}
for a comprehensive overview of syntax, dialects, and available options.

The standard format for a basic database connection URL is as follows: Username, password, host, and port are optional 
parameters based on the database type and specific configuration.
```
dialect://username:password@host:port/database
```
Here are some example connection strings:
```text
# SQLite, relative to Flask instance path
sqlite:///project.db

# PostgreSQL
postgresql://scott:tiger@localhost/project

# MySQL / MariaDB
mysql://scott:tiger@localhost/project
```

## **Default Driver Options**

To enhance usability for web applications, default options have been configured for SQLite and MySQL engines.

For SQLite, relative file paths are now relative to the **`root_path`** option rather than the current working directory. 
Additionally, **in-memory** databases utilize a static **`pool`** and **`check_same_thread`** to ensure seamless operation across multiple requests.

For `MySQL` (and `MariaDB`) servers, a default idle connection timeout of 8 hours has been set. This configuration helps avoid errors, 
such as 2013: Lost connection to `MySQL` server during query. To preemptively recreate connections before hitting this timeout, 
a default **`pool_recycle`** value of 2 hours (**7200** seconds) is applied.

## **Timeout**

Certain databases, including `MySQL` and `MariaDB`, might be set to close inactive connections after a certain duration, 
which can lead to errors like 2013: Lost connection to MySQL server during query. 
While this behavior is configured by default in MySQL and MariaDB, it could also be implemented by other database services.

If you encounter such errors, consider adjusting the pool_recycle option in the engine settings to a value less than the database's timeout.

Alternatively, you can explore setting pool_pre_ping if you anticipate frequent closure of connections, 
especially in scenarios like running the database in a container that may undergo periodic restarts.

For more in-depth information
on [dealing with disconnects](https://docs.sqlalchemy.org/core/pooling.html#dealing-with-disconnects){target="_blank"}, 
refer to SQLAlchemy's documentation on handling connection issues.

## **EllarSQLModule RegisterSetup**
As mentioned earlier, **EllarSQLModule** can be configured from the application through `EllarSQLModule.register_setup`. 
This process registers a [ModuleSetup](https://python-ellar.github.io/ellar/basics/dynamic-modules/#modulesetup){target="_blank"} factory
that depends on the Application Config object. 
The factory retrieves the `ELLAR_SQL` attribute from the config and validates the data before passing it to `EllarSQLModule` for setup.

It's essential to note 
that `ELLAR_SQL` will be a dictionary object with the [configuration parameters](#ellarsqlmodule-configuration-parameters) 
mentioned above as keys.

Here's a quick example:
```python title="db_learning/root_module.py"
from ellar.common import Module, exception_handler, IExecutionContext, JSONResponse, Response, IApplicationStartup
from ellar.app import App
from ellar.core import ModuleBase
from ellar_sql import EllarSQLModule, EllarSQLService
from .controller import UsersController


@Module(
    modules=[EllarSQLModule.register_setup()],
    controllers=[UsersController]
)
class ApplicationModule(ModuleBase, IApplicationStartup):
    async def on_startup(self, app: App) -> None:
        db_service = app.injector.get(EllarSQLService)
        db_service.create_all()
    
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse(dict(detail="Resource not found."), status_code=404)

```
Let's update `config.py`.

```python
import typing as t
...

class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    
    ELLAR_SQL: t.Dict[str, t.Any] = {
        'databases': {
            'default': 'sqlite:///app.db',
        },
        'echo': True,
        'migration_options': {
            'directory': 'migrations' # root directory will be determined based on where the module is instantiated.
        },
        'models': []
    }
```
The registered ModuleSetup factory reads the `ELLAR_SQL` value and configures the `EllarSQLModule` appropriately.

This approach is particularly useful when dealing with multiple environments. 
It allows for seamless modification of the **ELLAR_SQL** values in various environments such as 
Continuous Integration (CI), Development, Staging, or Production. 
You can easily change the settings for each environment 
and export the configurations as a string to be imported into `ELLAR_CONFIG_MODULE`.
