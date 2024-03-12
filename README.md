<p align="center">
  <a href="#" target="blank"><img src="https://python-ellar.github.io/ellar-sql/img/ellar_sql.png" width="200" alt="Ellar Logo" /></a>
</p>

![Test](https://github.com/python-ellar/ellar-sql/actions/workflows/test_full.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/python-ellar/ellar-sql)
[![PyPI version](https://badge.fury.io/py/ellar-sql.svg)](https://badge.fury.io/py/ellar-sql)
[![PyPI version](https://img.shields.io/pypi/v/ellar-sql.svg)](https://pypi.python.org/pypi/ellar-sql)
[![PyPI version](https://img.shields.io/pypi/pyversions/ellar-sql.svg)](https://pypi.python.org/pypi/ellar-sql)


## Introduction
EllarSQL Module adds support for `SQLAlchemy` and `Alembic` package to your Ellar application

## Installation
```shell
$(venv) pip install ellar-sql
```

This library was inspired by [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/)
## Features

- Migration
- Single/Multiple Database
- Pagination
- Compatible with SQLAlchemy tools


## **Usage**
In your ellar application, create a module called `db` or any name of your choice,
```shell
ellar create-module db
```
Then, in `models/base.py` define your model base as shown below:

```python
# db/models/base.py
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from ellar_sql.model import Model


class Base(Model):
  __base_config__ = {'as_base': True}
  __database__ = 'default'

  created_date: Mapped[datetime] = mapped_column(
      "created_date", DateTime, default=datetime.utcnow, nullable=False
  )

  time_updated: Mapped[datetime] = mapped_column(
      "time_updated", DateTime, nullable=False, default=datetime.utcnow, onupdate=func.now()
  )
```

Use `Base` to create other models, like users in `User` in 
```python
# db/models/users.py
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String)
```

### Configure Module
```python
# db/module.py
from ellar.app import App
from ellar.common import Module, IApplicationStartup
from ellar.core import ModuleBase
from ellar.di import Container
from ellar_sql import EllarSQLAlchemyModule, EllarSQLService

from .controllers import DbController

@Module(
    controllers=[DbController],
    providers=[],
    routers=[],
    modules=[
        EllarSQLAlchemyModule.setup(
            databases={
                'default': 'sqlite:///project.db',
            }, 
            echo=True, 
            migration_options={
                'directory': 'my_migrations_folder'
            },
            models=['db.models.users']
        )
    ]
)
class DbModule(ModuleBase, IApplicationStartup):
    """
    Db Module
    """

    async def on_startup(self, app: App) -> None:
        db_service = app.injector.get(EllarSQLService)
        db_service.create_all()

    def register_providers(self, container: Container) -> None:
        """for more complicated provider registrations, use container.register_instance(...) """
```

### Model Usage
Database session exist at model level and can be accessed through `model.get_db_session()` eg, `User.get_db_session()`
```python
# db/models/controllers.py
from ellar.common import Controller, ControllerBase, get, post, Body
from pydantic import EmailStr
from sqlalchemy import select

from .models.users import User


@Controller
class DbController(ControllerBase):
    @post("/users")
    async def create_user(self, username: Body[str], email: Body[EmailStr]):
        session = User.get_db_session()
        user = User(username=username, email=email)

        session.add(user)
        session.commit()
        
        return user.dict()


    @get("/users/{user_id:int}")
    def get_user_by_id(self, user_id: int):
        session = User.get_db_session()
        stmt = select(User).filter(User.id==user_id)
        user = session.execute(stmt).scalar()
        return user.dict()

    @get("/users")
    async def get_all_users(self):
        session = User.get_db_session()
        stmt = select(User)
        rows = session.execute(stmt.offset(0).limit(100)).scalars()
        return [row.dict() for row in rows]
```

## License

Ellar is [MIT licensed](LICENSE).
