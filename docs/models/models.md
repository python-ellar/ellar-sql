# **Models and Tables**
The `ellar_sql.model.Model` class acts as a factory for creating `SQLAlchemy` models, and 
associating the generated models with the corresponding **Metadata** through their designated **`__database__`** key.


This class can be configured through the `__base_config__` attribute, allowing you to specify how your `SQLAlchemy` model should be created. 
The `__base_config__` attribute can be of type `ModelBaseConfig`, which is a dataclass, or a dictionary with keys that 
match the attributes of `ModelBaseConfig`.

Attributes of `ModelBaseConfig`:

- **as_base**: Indicates whether the class should be treated as a `Base` class for other model definitions, similar to creating a Base from a [DeclarativeBase](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.DeclarativeBase){target="_blank"} or [DeclarativeBaseNoMeta](https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.DeclarativeBaseNoMeta){target="_blank"} class. *(Default: False)*
- **use_base**: Specifies the base classes that will be used to create the `SQLAlchemy` model. *(Default: [])*

## **Creating a Base Class**
`Model` treats each model as a standalone entity. Each instance of `model.Model` creates a distinct **declarative** base for itself, using the `__database__` key as a reference to determine its associated **Metadata**. Consequently, models sharing the same `__database__` key will utilize the same **Metadata** object.

Let's explore how we can create a `Base` model using `Model`, similar to the approach in traditional `SQLAlchemy`.

```python
from ellar_sql import model, ModelBaseConfig


class Base(model.Model):
    __base_config__ = ModelBaseConfig(as_base=True, use_bases=[model.DeclarativeBase])

    
assert issubclass(Base, model.DeclarativeBase)
```

If you are interested in [SQLAlchemy’s native support for data classes](https://docs.sqlalchemy.org/en/20/changelog/whatsnew_20.html#native-support-for-dataclasses-mapped-as-orm-models){target="_blank"}, 
then you can add `MappedAsDataclass` to `use_bases` as shown below:

```python
from ellar_sql import model, ModelBaseConfig


class Base(model.Model):
    __base_config__ = ModelBaseConfig(as_base=True, use_bases=[model.DeclarativeBase, model.MappedAsDataclass])

assert issubclass(Base, model.MappedAsDataclass)
```

In the examples above, `Base` classes are created, all subclassed from the `use_bases` provided, and with the `as_base` 
option, the factory creates the `Base` class as a `Base`.

## Create base with MetaData
You can also configure the SQLAlchemy object with a custom [`MetaData`](https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.MetaData){target="_blank"} object. 
For instance, you can define a specific **naming convention** for constraints, ensuring consistency and predictability in constraint names. 
This can be particularly beneficial during migrations, as detailed by [Alembic](https://alembic.sqlalchemy.org/en/latest/naming.html){target="_blank"}.

For example:

```python
from ellar_sql import model, ModelBaseConfig

class Base(model.Model):
    __base_config__ = ModelBaseConfig(as_base=True, use_bases=[model.DeclarativeBase])
    
    metadata = model.MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })
```

## **Abstract Models and Mixins**
If the desired behavior is only applicable to specific models rather than all models, 
you can use an abstract model base class to customize only those models. 
For example, if certain models need to track their creation or update **timestamps**, t
his approach allows for targeted customization.

```python
from datetime import datetime, timezone
from ellar_sql import model
from sqlalchemy.orm import Mapped, mapped_column

class TimestampModel(model.Model):
    __abstract__ = True
    created: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    
class BookAuthor(model.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    
class Book(TimestampModel):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
```

This can also be done with a mixin class, inherited separately.
```python
from datetime import datetime, timezone
from ellar_sql import model
from sqlalchemy.orm import Mapped, mapped_column

class TimestampModel:
    created: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    
class Book(model.Model, TimestampModel):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
```

## **Defining Models**
Unlike plain SQLAlchemy, **EllarSQL** models will automatically generate a table name if the `__tablename__` attribute is not set, 
provided a primary key column is defined.

```python
from ellar_sql import model


class User(model.Model):
    id: model.Mapped[int] = model.mapped_column(primary_key=True)
    username: model.Mapped[str] = model.mapped_column(unique=True)
    email: model.Mapped[str]

    
class UserAddress(model.Model):
    __tablename__ = 'user-address'
    id: model.Mapped[int] = model.mapped_column(primary_key=True)
    address: model.Mapped[str] = model.mapped_column(unique=True)

assert User.__tablename__ == 'user'
assert UserAddress.__tablename__ == 'user-address'
```
For a comprehensive guide on defining model classes declaratively, refer to 
[SQLAlchemy’s declarative documentation](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html){target="_blank"}. 
This resource provides detailed information and insights into the declarative approach for defining model classes.

## **Defining Tables**
The table class is designed to receive a table name, followed by **columns** and other table **components** such as constraints.

EllarSQL enhances the functionality of the SQLAlchemy Table 
by facilitating the selection of **Metadata** based on the `__database__` argument.

Directly creating a table proves particularly valuable when establishing **many-to-many** relationships. 
In such cases, the association table doesn't need its dedicated model class; rather, it can be conveniently accessed 
through the relevant relationship attributes on the associated models.

```python
from ellar_sql import model

author_book_m2m = model.Table(
    "author_book",
    model.Column("book_author_id", model.ForeignKey(BookAuthor.id), primary_key=True),
    model.Column("book_id", model.ForeignKey(Book.id), primary_key=True),
)
```

## **Quick Tutorial**
In this section, we'll delve into straightforward **CRUD** operations using the ORM objects. 
However, if you're not well-acquainted with SQLAlchemy,
feel free to explore their tutorial 
on [ORM](https://docs.sqlalchemy.org/tutorial/orm_data_manipulation.html){target="_blank"}
for a more comprehensive understanding.

Having understood, `Model` usage. Let's create a `User` model

```python
from ellar_sql import model


class User(model.Model):
    id: model.Mapped[int] = model.mapped_column(primary_key=True)
    username: model.Mapped[str] = model.mapped_column(unique=True)
    full_name: model.Mapped[str] = model.mapped_column(model.String)
```
We have created a `User` model but the data does not exist. Let's fix that

```python
from ellar.app import current_injector
from ellar_sql import EllarSQLService

db_service = current_injector.get(EllarSQLService)
db_service.create_all()
```

### **Insert**
To insert a data, you need a session
```python
import ellar.common as ecm
from .model import User

@ecm.post('/create')
def create_user():
    session = User.get_db_session()
    squidward = User(name="squidward", fullname="Squidward Tentacles")
    session.add(squidward)

    session.commit()
    
    return squidward.dict(exclude={'id'})
```
In the above illustration, `squidward`
data was converted to `dictionary` object by calling `.dict()` and excluding the `id` as shown below.

_It's important to note this functionality has not been extended to a relationship objects in an SQLAlchemy ORM object_.

### **Update**
To update, make changes to the ORM object and commit.
```python
import ellar.common as ecm
from .model import User


@ecm.put('/update')
def update_user():
    session = User.get_db_session()
    squidward = session.get(User, 1)
    
    squidward.fullname = 'EllarSQL'
    session.commit()
    
    return squidward.dict()

```
### **Delete**
To delete, pass the ORM object to `session.delete()`.
```python
import ellar.common as ecm
from .model import User


@ecm.delete('/delete')
def delete_user():
    session = User.get_db_session()
    squidward = session.get(User, 1)
    
    session.delete(squidward)
    session.commit()
    
    return ''

```
After modifying data, you must call `session.commit()` to commit the changes to the database.
Otherwise, changes may not be persisted to the database.

## **View Utilities**
EllarSQL provides some utility query functions to check missing entities and raise 404 Not found if not found.

- **get_or_404**: It will raise a 404 error if the row with the given id does not exist; otherwise, it will return the corresponding instance.
- **first_or_404**: It will raise a 404 error if the query does not return any results; otherwise, it will return the first result.
- **one_or_404**(): It will raise a 404 error if the query does not return exactly one result; otherwise, it will return the result.

```python
import ellar.common as ecm
from ellar_sql import get_or_404, one_or_404, model

@ecm.get("/user-by-id/{user_id:int}")
def user_by_id(user_id: int):
    user = get_or_404(User, user_id)
    return user.dict()

@ecm.get("/user-by-name/{name:str}")
def user_by_username(name: str):
    user = one_or_404(model.select(User).filter_by(name=name), error_message=f"No user named '{name}'.")
    return user.dict()
```

## **Accessing Metadata and Engines**

In the process of `EllarSQLModule` setup, three services are registered to the Ellar IoC container.

- `EllarSQLService`: Which manages models, metadata, engines and sessions
- `Engine`: SQLAlchemy Engine of the default database configuration
- `Session`SQLAlchemy Session of the default database configuration

Although with `EllarSQLService` you can get the `engine` and `session`. It's there for easy of access.

```python
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from ellar.app import current_injector
from ellar_sql import EllarSQLService

db_service = current_injector.get(EllarSQLService)

assert isinstance(db_service.engine, sa.Engine)
assert isinstance(db_service.session_factory(), sa_orm.Session)
```
#### **Important Constraints**
- EllarSQLModule `databases` options for `SQLAlchemy.ext.asyncio.AsyncEngine` will register `SQLAlchemy.ext.asyncio.AsyncEngine`
  and `SQLAlchemy.ext.asyncio.AsyncSession`
- EllarSQLModule `databases` options for `SQLAlchemy.Engine` will register `SQLAlchemy.Engine` and `SQLAlchemy.orm.Session`.
- `EllarSQL.get_all_metadata()` retrieves all configured metadatas
- `EllarSQL.get_metadata()` retrieves metadata by `__database__` key or `default` is no parameter is passed.

```python
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from ellar.app import current_injector

# get engine from DI
default_engine = current_injector.get(sa.Engine)
# get session from DI
session = current_injector.get(sa_orm.Session)


assert isinstance(default_engine, sa.Engine)
assert isinstance(session, sa_orm.Session)
```
For Async Database options
```python
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from ellar.app import current_injector

# get engine from DI
default_engine = current_injector.get(AsyncEngine)
# get session from DI
session = current_injector.get(AsyncSession)


assert isinstance(default_engine, AsyncEngine)
assert isinstance(session, AsyncSession)
```
