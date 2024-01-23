# **Quick Start**
In this segment, we will walk through the process of configuring **EllarSQL** within your Ellar application, 
ensuring that all essential services are registered, configurations are set, and everything is prepared for immediate use.

Before we delve into the setup instructions, it is assumed that you possess a comprehensive 
understanding of how [Ellar Modules](https://python-ellar.github.io/ellar/basics/dynamic-modules/#module-dynamic-setup){target="_blank"} 
operate.

## **Installation**
Let us install all the required packages, assuming that your Python environment has been properly configured:

#### **For Existing Project:**
```shell
pip install ellar-sql
```

#### **For New Project**:
```shell
pip install ellar ellar-cli ellar-sql
```

After a successful package installation, we need to scaffold a new project using `ellar` cli tool
```shell
ellar new db-learning
```
This will scaffold `db-learning` project with necessary file structure shown below.
```
path/to/db-learning/
├─ db_learning/
│  ├─ apps/
│  │  ├─ __init__.py
│  ├─ core/
│  ├─ config.py
│  ├─ domain
│  ├─ root_module.py
│  ├─ server.py
│  ├─ __init__.py
├─ tests/
│  ├─ __init__.py
├─ pyproject.toml
├─ README.md
```
Next, in `db_learning/` directory, we need to create a `models.py`. It will hold all our SQLAlchemy ORM Models for now.

## **Creating a Model**
In `models.py`, we use `ellar_sql.model.Model` to create our SQLAlchemy ORM Models.

```python title="db_learning/model.py"
from ellar_sql import model


class User(model.Model):
    id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)
    username: model.Mapped[str] = model.mapped_column(model.String, unique=True, nullable=False)
    email: model.Mapped[str] = model.mapped_column(model.String)
```

!!!info
    `ellar_sql.model` also exposes `sqlalchemy`, `sqlalchemy.orm` and `sqlalchemy.event` imports just for ease of import reference

## **Create A UserController**
Let's create a controller that exposes our user data.

```python title="db_learning/controller.py"
import ellar.common as ecm
from ellar.pydantic import EmailStr
from ellar_sql import model, get_or_404
from .models import User


@ecm.Controller
class UsersController(ecm.ControllerBase):
    @ecm.post("/users")
    def create_user(self, username: ecm.Body[str], email: ecm.Body[EmailStr], session: ecm.Inject[model.Session]):
        user = User(username=username, email=email)

        session.add(user)
        session.commit()
        session.refresh(user)
        
        return user.dict()

    @ecm.get("/users/{user_id:int}")
    def user_by_id(self, user_id: int):
        user = get_or_404(User, user_id)
        return user.dict()

    @ecm.get("/")
    async def user_list(self, session: ecm.Inject[model.Session]):
        stmt = model.select(User)
        rows = session.execute(stmt.offset(0).limit(100)).scalars()
        return [row.dict() for row in rows]
    
    @ecm.get("/{user_id:int}")
    async def user_delete(self, user_id: int, session: ecm.Inject[model.Session]):
        user = get_or_404(User, user_id)
        session.delete(user)
        return {'detail': f'User id={user_id} Deleted successfully'}
```

## **EllarSQLModule Setup**
In the `root_module.py` file, two main tasks need to be performed:

1. Register the `UsersController` to make the `/users` endpoint available when starting the application.
2. Configure the `EllarSQLModule`, which will set up and register essential services such as `EllarSQLService`, `Session`, and `Engine`.

```python title="db_learning/root_module.py"
from ellar.common import Module, exception_handler, IExecutionContext, JSONResponse, Response, IApplicationStartup
from ellar.app import App
from ellar.core import ModuleBase
from ellar_sql import EllarSQLModule, EllarSQLService
from .controller import UsersController

@Module(
    modules=[EllarSQLModule.setup(
        databases={
            'default': {
                'url': 'sqlite:///app.db',
                'echo': True
            }
        },
        migration_options={'directory': 'migrations'}
    )],
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

In the provided code snippet:

- We registered `UserController` and `EllarSQLModule` with specific configurations for the database and migration options. For more details on [`EllarSQLModule` configurations](./configuration.md#ellarsqlmodule-config).

- In the `on_startup` method, we obtained the `EllarSQLService` from the Ellar Dependency Injection container using `EllarSQLModule`. Subsequently, we invoked the `create_all()` method to generate the necessary SQLAlchemy tables.

With these configurations, the application is now ready for testing.
```shell
ellar runserver --reload
```
Additionally, please remember to uncomment the configurations for the `OpenAPIModule` in the `server.py` 
file to enable visualization and interaction with the `/users` endpoint.

Once done, 
you can access the OpenAPI documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs){target="_blank"}.
