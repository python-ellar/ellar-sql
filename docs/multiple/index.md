# **Multiple Databases**

SQLAlchemy has the capability to establish connections with multiple databases simultaneously, referring to these connections as "binds."

EllarSQL simplifies the management of binds by associating each engine with a short string identifier, "__database__." 
Subsequently, each model and table is linked to a "__database__," and during a query, 
the session selects the appropriate engine based on the "__database__" of the entity being queried. 
In the absence of a specified "__database__," the default engine is employed.

## Configuring Multiple Databases

In EllarSQL, database configuration begins with the setup of the default database, 
followed by additional databases, as exemplified in the `EllarSQLModule` configurations:

```python
from ellar_sql import EllarSQLModule

EllarSQLModule.setup(
    databases={
        "default": "postgresql:///main",
        "meta": "sqlite:////path/to/meta.db",
        "auth": {
            "url": "mysql://localhost/users",
            "pool_recycle": 3600,
        },
    },
    migration_options={'directory': 'migrations'}
)
```

## Defining Models and Tables with Different Databases

EllarSQL creates metadata and an engine for each configured database. 
Models and tables associated with a specific database key are registered with the corresponding metadata. 
During a session query, the session employs the related engine.

To designate the database for a model, set the "__database__" class attribute. 
Not specifying a database key is equivalent to setting it to `default`:

### In Models

```python
from ellar_sql import model

class User(model.Model):
    __database__ = "auth"
    id = model.Column(model.Integer, primary_key=True)
```
Models inheriting from an already existing model will share the same `database` key unless they are overriden.

!!!info
    Its importance to not that `model.Model` has `__database__` value equals `default`

### In Tables
To specify the database for a table, utilize the `__database__` keyword argument:

```python
from ellar_sql import model

user_table = model.Table(
    "user",
    model.Column("id", model.Integer, primary_key=True),
    __database__="auth",
)
```

!!!info
    Ultimately, the session references the database key associated with the metadata or table, an association established during creation. 
    Consequently, changing the **database** key after creating a model or table has **no effect**.

## Creating and Dropping Tables

The `create_all()` and `drop_all()` methods operating are all part of the `EllarSQLService`.
It also requires the `database` argument to target a specific database. 

```python
# Create tables for all binds
from ellar.app import current_injector
from ellar_sql import EllarSQLService

db_service = current_injector.get(EllarSQLService)

# Create tables for all configured databases
db_service.create_all()

# Create tables for the 'default' and "auth" databases
db_service.create_all('default', "auth")

# Create tables for the "meta" database
db_service.create_all("meta")

# Drop tables for the 'default' database
db_service.drop_all('default')
```
