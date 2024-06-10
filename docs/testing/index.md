# **Testing EllarSQL Models**
There are various approaches to testing SQLAlchemy models, but in this section, we will focus on setting 
up a good testing environment for EllarSQL models using the 
Ellar [Test](https://python-ellar.github.io/ellar/basics/testing/){target="_blank"} factory and pytest.

For an effective testing environment, it is recommended to utilize the `EllarSQLModule.register_setup()` 
approach to set up the **EllarSQLModule**. This allows you to add a new configuration for `ELLAR_SQL` 
specific to your testing database, preventing interference with production or any other databases in use.

### **Defining TestConfig**
There are various methods for configuring test settings in Ellar, 
as outlined 
[here](https://python-ellar.github.io/ellar/basics/testing/#overriding-application-conf-during-testing){target="_blank"}.
However, in this section, we will adopt the 'in a file' approach.

Within the `db_learning/config.py` file, include the following code:

```python title="db_learning/config.py"
import typing as t
...

class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    # Configuration through Config
    ELLAR_SQL: t.Dict[str, t.Any] = {
        'databases': {
            'default': 'sqlite:///project.db',
        },
        'echo': True,
        'migration_options': {
            'directory': 'migrations'
        },
        'models': ['models']
    }

class TestConfig(BaseConfig):
    DEBUG = False
    
    ELLAR_SQL: t.Dict[str, t.Any] = {
        **DevelopmentConfig.ELLAR_SQL, 
        'databases': {
            'default': 'sqlite:///test.db',
        },
        'echo': False,
    }
```

This snippet demonstrates the 'in a file' approach to setting up the `TestConfig` class within the same `db_learning/config.py` file.

#### **Changes made:**
1. Updated the `databases` section to use `sqlite+aiosqlite:///test.db` for the testing database.
2. Set `echo` to `True` to enable SQLAlchemy output during testing for cleaner logs.
3. Preserved the `migration_options` and `models` configurations from `DevelopmentConfig`.

Also, feel free to further adjust it based on your specific testing requirements!

## **Test Fixtures**
After defining `TestConfig`, we need to add some pytest fixtures to set up **EllarSQLModule** and another one 
that returns a `session` for testing purposes. Additionally, we need to export `ELLAR_CONFIG_MODULE` 
to point to the newly defined **TestConfig**.

```python title="tests/conftest.py"
import os
import pytest
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.testing import Test
from ellar_sql import EllarSQLService
from db_learning.root_module import ApplicationModule

# Setting the ELLAR_CONFIG_MODULE environment variable to TestConfig
os.environ.setdefault(ELLAR_CONFIG_MODULE, "db_learning.config:TestConfig")

# Fixture for creating a test module
@pytest.fixture(scope='session')
def tm():
    test_module = Test.create_test_module(modules=[ApplicationModule])
    yield test_module

# Fixture for creating a database session for testing
@pytest.fixture(scope='session')
def db(tm):
    db_service = tm.get(EllarSQLService)
    
    # Creating all tables
    db_service.create_all()

    yield

    # Dropping all tables after the tests
    db_service.drop_all()

# Fixture for creating a database session for testing
@pytest.fixture(scope='session')
def db_session(db, tm):
    db_service = tm.get(EllarSQLService)

    yield db_service.session_factory()

    # Removing the session factory
    db_service.session_factory.remove()
```

The provided fixtures help in setting up a testing environment for EllarSQL models. 
The `Test.create_test_module` method creates a **TestModule** for initializing your Ellar application, 
and the `db_session` fixture initializes a database session for testing, creating and dropping tables as needed. 

If you are working with asynchronous database drivers, you can convert `db_session` 
into an async function to handle coroutines seamlessly.

## **Alembic Migration with Test Fixture**
In cases where there are already generated database migration files, and there is a need to apply migrations during testing, this can be achieved as shown in the example below:

```python title="tests/conftest.py"
import os
import pytest
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.testing import Test
from ellar_sql import EllarSQLService
from ellar_sql.cli.handlers import CLICommandHandlers
from db_learning.root_module import ApplicationModule

# Setting the ELLAR_CONFIG_MODULE environment variable to TestConfig
os.environ.setdefault(ELLAR_CONFIG_MODULE, "db_learning.config:TestConfig")

# Fixture for creating a test module
@pytest.fixture(scope='session')
def tm():
    test_module = Test.create_test_module(modules=[ApplicationModule])
    yield test_module


# Fixture for creating a database session for testing
@pytest.fixture(scope='session')
async def db(tm):
    db_service = tm.get(EllarSQLService)
    
    # Applying migrations using Alembic
    async with tm.create_application().application_context():
        cli = CLICommandHandlers(db_service)
        cli.migrate()

    yield

    # Downgrading migrations after testing
    async with tm.create_application().application_context():
        cli = CLICommandHandlers(db_service)
        cli.downgrade()

# Fixture for creating an asynchronous database session for testing
@pytest.fixture(scope='session')
async def db_session(db, tm):
    db_service = tm.get(EllarSQLService)
    
    yield db_service.session_factory()

    # Removing the session factory
    db_service.session_factory.remove()
```

The `CLICommandHandlers` class wraps all `Alembic` functions executed through the Ellar command-line interface. 
It can be used in conjunction with the application context to initialize all model tables during testing as shown in the illustration above. 
`db_session` pytest fixture also ensures that migrations are applied and then downgraded after testing, 
maintaining a clean and consistent test database state.

## **Testing a Model**
After setting up the testing database and creating a session, let's test the insertion of a user model into the database.

In `db_learning/models.py`, we have a user model:

```python title="db_learning/model.py"
from ellar_sql import model

class User(model.Model):
    id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)
    username: model.Mapped[str] = model.mapped_column(model.String, unique=True, nullable=False)
    email: model.Mapped[str] = model.mapped_column(model.String)
```

Now, create a file named `test_user_model.py`:

```python title="tests/test_user_model.py"
import pytest
import sqlalchemy.exc as sa_exc
from db_learning.models import User

def test_username_must_be_unique(db_session):
    # Creating and adding the first user
    user1 = User(username='ellarSQL', email='ellarsql@gmail.com')
    db_session.add(user1)
    db_session.commit()

    # Attempting to add a second user with the same username
    user2 = User(username='ellarSQL', email='ellarsql2@gmail.com')
    db_session.add(user2)
    
    # Expecting an IntegrityError due to unique constraint violation
    with pytest.raises(sa_exc.IntegrityError):
        db_session.commit()
```

In this test, we are checking whether the unique constraint on the `username` 
field is enforced by attempting to insert two users with the same username. 
The test expects an `IntegrityError` to be raised, indicating a violation of the unique constraint. 
This ensures that the model behaves correctly and enforces the specified uniqueness requirement.

## **Testing Factory Boy**
[factory-boy](https://pypi.org/project/factory-boy/){target="_blank"} provides a convenient and flexible way to create mock objects, supporting various ORMs like Django, MongoDB, and SQLAlchemy. EllarSQL extends `factory.alchemy.SQLAlchemy` to offer a Model factory solution compatible with both synchronous and asynchronous database drivers.

To get started, you need to install `factory-boy`:

```shell
pip install factory-boy
```

Now, let's create a factory for our user model in `tests/factories.py`:

```python title="tests/factories.py"
import factory
from db_learning.models import User
from ellar.app import current_injector
from sqlalchemy.orm import Session

from ellar_sql.factory import SESSION_PERSISTENCE_FLUSH, EllarSQLFactory


def _get_session():
    session = current_injector.get(Session)
    return session

class UserFactory(EllarSQLFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = SESSION_PERSISTENCE_FLUSH
        sqlalchemy_session_factory = _get_session

    username = factory.Faker('username')
    email = factory.Faker('email')
```

The `UserFactory` depends on a database Session as you see from `_get_session()` function.
We need to ensure that test fixture provides `ApplicationContext` for `current_injector` to work.

So in `tests/conftest.py`, we make `tm` test fixture to run application context:

```python title="tests/conftest.py"
import os

import pytest
from db_learning.root_module import ApplicationModule
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.testing import Test
from ellar.threading.sync_worker import execute_async_context_manager

from ellar_sql import EllarSQLService

os.environ.setdefault(ELLAR_CONFIG_MODULE, "db_learning.config:TestConfig")

@pytest.fixture(scope='session')
def tm():
    test_module = Test.create_test_module(modules=[ApplicationModule])
    app = test_module.create_application()
    
    with execute_async_context_manager(app.application_context()):
        yield test_module

# Fixture for creating a database session for testing
@pytest.fixture(scope='session')
def db(tm):
    db_service = tm.get(EllarSQLService)
    
    # Creating all tables
    db_service.create_all()

    yield

    # Dropping all tables after the tests
    db_service.drop_all()
```

With this setup, we can rewrite our `test_username_must_be_unique` test using `UserFactory` and `factory_session`:

```python title="tests/test_user_model.py"
import pytest
import sqlalchemy.exc as sa_exc
from .factories import UserFactory

def test_username_must_be_unique(factory_session):
    user1 = UserFactory()
    with pytest.raises(sa_exc.IntegrityError):
        UserFactory(username=user1.username)
```

This test yields the same result as before. 
Refer to the [factory-boy documentation](https://factoryboy.readthedocs.io/en/stable/orms.html#sqlalchemy) 
for more features and tutorials.
